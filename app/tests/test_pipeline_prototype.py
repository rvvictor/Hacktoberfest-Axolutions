"""DEMO_MODE (no keys, what a judge runs) still builds the prototype from the recorded app and checks it for real."""

from app.schemas import EventType
from app.services import generator, stages, store
from app.tests.test_pipeline import _approve, _create, client  # noqa: F401  (client is a fixture)


def _events(run_id, etype):
    return [e for _, e in store.list_events(run_id) if e.type is etype]


def _to_quality(client):  # noqa: F811  (pytest fixture imported above)
    run_id = _create(client)
    client.post(f"/api/runs/{run_id}/answers", json={"answers": ["a", "b", "c"]})
    _approve(client, run_id, 1)
    _approve(client, run_id, 2)
    return run_id


def test_demo_run_serves_the_recorded_speedhack_app_and_checks_it(client):  # noqa: F811
    run_id = _to_quality(client)
    proto = _events(run_id, EventType.prototype_ready)[-1]
    assert proto.payload["generator"] == "speedhack" and proto.payload["url"] == f"/api/prototypes/{run_id}/"
    assert proto.demo_data and proto.payload["demo_data"] is True
    assert generator.prototype_path(run_id).read_text() == generator.SPEEDHACK_RECORDED.read_text()
    page = client.get(proto.payload["url"])
    assert page.status_code == 200 and "sandbox allow-scripts" in page.headers["content-security-policy"]
    checks = {e.payload["name"]: e for e in _events(run_id, EventType.quality_check)}
    assert {"lint", "secrets"} <= checks.keys() and "rls" not in checks  # real checks, not the recorded report
    assert all(e.payload["passed"] and e.demo_data for e in checks.values())


def test_demo_stage_that_fails_replays_the_recorded_run(client, monkeypatch):  # noqa: F811
    def boom(ctx):
        raise RuntimeError("generator unavailable")

    monkeypatch.setitem(stages.ADAPTERS, 7, boom)
    monkeypatch.setitem(stages.ADAPTERS, 8, boom)
    run_id = _to_quality(client)
    assert _events(run_id, EventType.prototype_ready)[-1].payload["generator"] == "planb"
    assert "rls" in {e.payload["name"] for e in _events(run_id, EventType.quality_check)}
