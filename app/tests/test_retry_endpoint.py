"""POST /api/runs/{id}/retry runs the failed stage again, in the background (HACK-070)."""
import itertools

import pytest
import respx
from fastapi.testclient import TestClient

from app.config import settings
from app.main import app
from app.schemas import EventType
from app.services import pipeline, store
from app.tests.test_stages import (  # noqa: F401  (fixtures and helpers shared with the stage tests)
    _approve,
    _real_board_with_mocked_miro,
    _start,
    live_services,
)
from app.tests.test_stages import client as live_client  # noqa: F401


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "DATA_DIR", tmp_path)
    monkeypatch.setattr(settings, "DEMO_MODE", False)
    monkeypatch.setenv("DEMO_SPEED", "0")
    monkeypatch.setattr(pipeline, "REGISTRY", {})
    return TestClient(app)


def _failed_run(client) -> str:
    """A live run whose research stage (3) failed on its first attempt."""
    calls = {"n": 0}

    def flaky(ctx):
        calls["n"] += 1
        if calls["n"] == 1:
            raise RuntimeError("down")
        return [("research_item", {"competitor": "Acme", "url": "https://acme.test/pricing"})]

    pipeline.register(3, flaky)
    pipeline.register(4, lambda ctx: [])
    run_id = client.post("/api/projects", json={"mode": "dev", "idea": "catálogo de bombas"}).json()["run_id"]
    client.post(f"/api/runs/{run_id}/answers", json={"answers": ["a"]})
    return run_id


def test_retry_a_failed_run_is_accepted_and_runs_the_stage_again(client):
    run_id = _failed_run(client)
    assert client.get(f"/api/runs/{run_id}").json()["awaiting"] == "retry:3"

    r = client.post(f"/api/runs/{run_id}/retry")

    assert r.status_code == 200
    assert r.json() == {"run_id": run_id, "accepted": True}
    state = client.get(f"/api/runs/{run_id}").json()
    assert state["status"] != "failed" and state["awaiting"] != "retry:3"
    items = [e for _, e in store.list_events(run_id) if e.type is EventType.research_item]
    assert [e.payload["competitor"] for e in items] == ["Acme"]


def test_retry_twice_in_a_row_is_a_conflict_the_second_time(client):
    run_id = _failed_run(client)
    assert client.post(f"/api/runs/{run_id}/retry").status_code == 200
    assert client.post(f"/api/runs/{run_id}/retry").status_code == 409


def test_retry_a_run_that_has_not_failed_is_a_conflict(client, monkeypatch):
    monkeypatch.setattr(settings, "DEMO_MODE", True)
    run_id = client.post("/api/projects", json={"mode": "dev", "idea": "catálogo de bombas"}).json()["run_id"]
    client.post(f"/api/runs/{run_id}/answers", json={"answers": ["a"]})  # now waits on approval:1

    r = client.post(f"/api/runs/{run_id}/retry")

    assert r.status_code == 409
    assert client.get(f"/api/runs/{run_id}").json()["awaiting"] == "approval:1"  # untouched


def test_retry_an_unknown_run_is_not_found(client):
    assert client.post("/api/runs/does-not-exist/retry").status_code == 404


def test_retry_through_the_endpoint_does_not_create_a_second_miro_board(live_client, live_services, monkeypatch):
    ids = itertools.count(1)
    with respx.mock() as router:
        _real_board_with_mocked_miro(monkeypatch, router, ids, first_note_status=[None, None, None, None, "boom"])
        run_id = _start(live_client)
        _approve(live_client, run_id, 1)
        boards = router.routes[0]
        assert boards.call_count == 1
        assert live_client.get(f"/api/runs/{run_id}").json()["awaiting"] == "retry:5"

        assert live_client.post(f"/api/runs/{run_id}/retry").status_code == 200

        assert boards.call_count == 1  # the retry reused the board of the failed attempt
    assert live_client.get(f"/api/runs/{run_id}").json()["awaiting"] == "approval:2"
