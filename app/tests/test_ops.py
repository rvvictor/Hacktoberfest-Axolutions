import json
import sqlite3

import pytest
from fastapi.testclient import TestClient

from app.config import settings
from app.main import app
from app.services import costs

client = TestClient(app)


@pytest.fixture(autouse=True)
def data_dir(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "DATA_DIR", tmp_path)
    monkeypatch.setattr(settings, "DEMO_MODE", True)
    return tmp_path


def test_empty_store_serves_labeled_demo_run() -> None:
    body = client.get("/api/ops/runs").json()
    assert len(body["runs"]) == 1
    run = body["runs"][0]
    assert run["demo_data"] is True
    assert len(run["stages"]) == 9
    assert run["total_usd"] == pytest.approx(sum(s["usd"] for s in run["steps"]))
    assert all(s["estimated"] and s["source_url"].startswith("https://") for s in run["steps"])


def test_no_demo_when_disabled(monkeypatch) -> None:
    monkeypatch.setattr(settings, "DEMO_MODE", False)
    assert client.get("/api/ops/runs").json()["runs"] == []


def test_real_run_costs_durations_and_failures(data_dir) -> None:
    conn = sqlite3.connect(data_dir / "speedhack.db")
    conn.executescript(
        """
        CREATE TABLE runs (run_id TEXT PRIMARY KEY, project_id TEXT, stage INTEGER, status TEXT,
            awaiting TEXT, approvals TEXT, demo_data INTEGER, created REAL);
        CREATE TABLE events (seq INTEGER PRIMARY KEY AUTOINCREMENT, run_id TEXT, event TEXT);
        CREATE TABLE costs (run_id TEXT, step TEXT, usd REAL, PRIMARY KEY (run_id, step));
        """
    )
    conn.execute("INSERT INTO runs VALUES ('r1','p1',3,'failed',NULL,'[]',0,1.0)")
    for stage, type_, ts, payload in [
        (1, "stage_started", 0.0, {}), (1, "stage_done", 2.0, {}),
        (2, "stage_started", 2.5, {}), (2, "error", 4.0, {"message": "timeout"}),
    ]:
        event = {"run_id": "r1", "stage": stage, "type": type_, "payload": payload, "ts": ts, "demo_data": False}
        conn.execute("INSERT INTO events (run_id, event) VALUES ('r1', ?)", (json.dumps(event),))
    conn.executemany("INSERT INTO costs VALUES ('r1', ?, ?)", [("clarify", 0.5), ("pitch", 1.0)])
    conn.commit()
    conn.close()

    run = client.get("/api/ops/runs").json()["runs"][0]
    assert run["run_id"] == "r1" and run["demo_data"] is False
    assert run["total_usd"] == 1.5
    assert run["budget_used"] == pytest.approx(1.5 / costs.PLAN_BUDGET_USD)
    assert run["failures"] == 1
    by_stage = {s["name"]: s for s in run["stages"]}
    assert by_stage["intake"]["duration_s"] == 2.0 and by_stage["intake"]["status"] == "done"
    assert by_stage["clarify"]["status"] == "failed" and by_stage["clarify"]["error"] == "timeout"
    assert by_stage["research"]["status"] == "pending"
    units = {s["step"]: s["unit"] for s in run["steps"]}
    assert units == {"clarify": "tokens", "pitch": "minutes"}
