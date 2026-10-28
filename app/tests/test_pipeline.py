import json

import pytest
from fastapi.testclient import TestClient

from app.config import settings
from app.main import app
from app.schemas import EventType
from app.services import pipeline, store


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "DATA_DIR", tmp_path)
    monkeypatch.setattr(settings, "DEMO_MODE", True)
    monkeypatch.setenv("DEMO_SPEED", "0")
    monkeypatch.setattr(pipeline, "REGISTRY", {})
    return TestClient(app)


def _create(client):
    r = client.post("/api/projects", json={"mode": "dev", "idea": "SaaS de gastos"})
    assert r.status_code == 201
    return r.json()["run_id"]


def _approve(client, run_id, n, approved=True, comment=None):
    return client.post(f"/api/runs/{run_id}/approvals/{n}", json={"approved": approved, "comment": comment})


def _events(client, run_id):
    with client.stream("GET", f"/api/runs/{run_id}/events") as r:
        assert r.headers["content-type"].startswith("text/event-stream")
        return [json.loads(line[5:]) for line in r.iter_lines() if line.startswith("data:")]


def test_full_run_with_three_approvals(client):
    run_id = _create(client)
    state = client.get(f"/api/runs/{run_id}").json()
    assert state["awaiting"] == "answers" and state["stage"] == 2

    assert client.post(f"/api/runs/{run_id}/answers", json={"answers": ["sí", "3 roles", "email"]}).status_code == 200
    state = client.get(f"/api/runs/{run_id}").json()
    assert state["awaiting"] == "approval:1" and state["status"] == "awaiting_approval"
    assert state["spec"]["version"] == 1

    for n, awaiting in ((1, "approval:2"), (2, "approval:3"), (3, None)):
        assert _approve(client, run_id, n).status_code == 200
        state = client.get(f"/api/runs/{run_id}").json()
        assert state["awaiting"] == awaiting
    assert state["status"] == "done" and state["demo_data"] is True
    assert [a["state"] for a in state["approvals"]] == ["approved"] * 3

    events = _events(client, run_id)
    assert {e["stage"] for e in events} == set(range(1, 10))
    assert all(e["demo_data"] for e in events)
    assert [e["payload"]["approval"] for e in events if e["type"] == "approval_given"] == [1, 2, 3]
    assert [e["ts"] for e in events] == sorted(e["ts"] for e in events)


def test_sse_replays_past_events_and_resumes_after_id(client):
    run_id = _create(client)
    client.post(f"/api/runs/{run_id}/answers", json={"answers": ["a"]})
    for n in (1, 2, 3):
        _approve(client, run_id, n)
    all_events = _events(client, run_id)
    with client.stream("GET", f"/api/runs/{run_id}/events?after=2") as r:
        tail = [json.loads(l[5:]) for l in r.iter_lines() if l.startswith("data:")]
    assert tail == all_events[2:]


def test_rejection_goes_back_one_stage_with_comment_and_versions_the_spec(client):
    run_id = _create(client)
    client.post(f"/api/runs/{run_id}/answers", json={"answers": ["a"]})
    assert _approve(client, run_id, 1, approved=False, comment="falta multiempresa").status_code == 200
    state = client.get(f"/api/runs/{run_id}").json()
    assert state["awaiting"] == "approval:1" and state["spec"]["version"] == 2
    assert [a["state"] for a in state["approvals"]] == ["pending"] * 3
    events = _events_until_gate(client, run_id)
    rejected = [e for e in events if e["type"] == "approval_rejected"]
    assert rejected[0]["payload"] == {"approval": 1, "comment": "falta multiempresa"}
    assert store.get_spec(run_id, 1)["version"] == 1


def _events_until_gate(client, run_id):
    return [e.model_dump(mode="json") for _, e in store.list_events(run_id)]


def test_wrong_calls_are_rejected(client):
    run_id = _create(client)
    assert _approve(client, run_id, 1).status_code == 409  # still waiting for answers
    assert _approve(client, run_id, 4).status_code == 404
    assert client.get("/api/runs/nope").status_code == 404
    assert client.post("/api/projects", json={"mode": "dev", "idea": ""}).status_code == 422
    client.post(f"/api/runs/{run_id}/answers", json={"answers": ["a"]})
    assert client.post(f"/api/runs/{run_id}/answers", json={"answers": ["a"]}).status_code == 409
    assert _approve(client, run_id, 2).status_code == 409  # approval 1 comes first


def test_failing_provider_falls_back_to_recorded_run(client, monkeypatch):
    monkeypatch.setattr(settings, "DEMO_MODE", False)

    def broken(ctx):
        raise RuntimeError("provider down")

    pipeline.register(3, broken)
    run_id = _create(client)
    client.post(f"/api/runs/{run_id}/answers", json={"answers": ["a"]})
    research = [e for _, e in store.list_events(run_id) if e.type is EventType.research_item]
    assert research and all(e.demo_data for e in research)
    assert client.get(f"/api/runs/{run_id}").json()["status"] == "awaiting_approval"


def test_real_provider_is_used_validated_and_costed(client, monkeypatch):
    monkeypatch.setattr(settings, "DEMO_MODE", False)
    seen = {}

    def research(ctx):
        seen["answers"] = ctx.answers
        ctx.add_cost(0.02)
        return [("research_item", {"competitor": "Acme", "url": "https://acme.test/pricing"})]

    pipeline.register(3, research)
    run_id = _create(client)
    client.post(f"/api/runs/{run_id}/answers", json={"answers": ["multiempresa"]})
    items = [e for _, e in store.list_events(run_id) if e.type is EventType.research_item]
    assert [e.payload["competitor"] for e in items] == ["Acme"] and not items[0].demo_data
    assert seen["answers"] == ["multiempresa"]
    assert client.get(f"/api/runs/{run_id}").json()["cost_by_step"] == {"research": 0.02}


def test_provider_with_invalid_payload_falls_back(client, monkeypatch):
    monkeypatch.setattr(settings, "DEMO_MODE", False)
    pipeline.register(3, lambda ctx: [("research_item", {"competitor": "Acme"})])  # no url: breaks the contract
    run_id = _create(client)
    client.post(f"/api/runs/{run_id}/answers", json={"answers": ["a"]})
    items = [e for _, e in store.list_events(run_id) if e.type is EventType.research_item]
    assert items and all(e.demo_data for e in items)


def test_external_ids_are_stored_per_stage(client):
    run_id = _create(client)
    client.post(f"/api/runs/{run_id}/answers", json={"answers": ["a"]})
    _approve(client, run_id, 1)
    ids = store.get_externals(run_id, 5)
    assert ids and all(k.startswith("miro:") for k in ids)
