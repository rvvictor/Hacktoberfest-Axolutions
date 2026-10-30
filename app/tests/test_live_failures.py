"""A failed stage in a real run says so; it never shows another project's recording (HACK-064)."""
import asyncio

import httpx
import pytest
import respx
from fastapi.testclient import TestClient

from app.config import settings
from app.main import app
from app.schemas import EventType
from app.schemas.content import Architecture
from app.services import miro, pipeline, store


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "DATA_DIR", tmp_path)
    monkeypatch.setenv("DEMO_SPEED", "0")
    monkeypatch.setattr(pipeline, "REGISTRY", {})
    return TestClient(app)


def _run_to_research(client) -> str:
    run_id = client.post("/api/projects", json={"mode": "dev", "idea": "catálogo de bombas"}).json()["run_id"]
    client.post(f"/api/runs/{run_id}/answers", json={"answers": ["a"]})
    return run_id


def _events(run_id, stage, etype):
    return [e for _, e in store.list_events(run_id) if e.stage == stage and e.type is etype]


def _state(client, run_id):
    return client.get(f"/api/runs/{run_id}").json()


def test_live_failure_emits_error_and_never_replays_the_recording(client, monkeypatch):
    monkeypatch.setattr(settings, "DEMO_MODE", False)

    def broken(ctx):
        raise RuntimeError("Miro answered 500")

    pipeline.register(3, broken)
    run_id = _run_to_research(client)
    assert _events(run_id, 3, EventType.research_item) == []  # no other project's competitors
    errors = _events(run_id, 3, EventType.error)
    assert len(errors) == 1
    message = errors[0].payload["message"]
    assert "Tavily" in message and "Reintentar" in message  # names the provider, says what to do
    assert not errors[0].demo_data
    state = _state(client, run_id)
    assert state["status"] == "failed" and state["awaiting"] == "retry:3"
    assert state["stage"] == 3  # the run waits on the stage that failed


def test_demo_mode_keeps_replaying_the_recording(client, monkeypatch):
    monkeypatch.setattr(settings, "DEMO_MODE", True)
    run_id = _run_to_research(client)
    assert _events(run_id, 3, EventType.research_item)
    assert _events(run_id, 3, EventType.error) == []
    assert _state(client, run_id)["status"] == "awaiting_approval"


def test_failure_message_does_not_leak_the_exception_text(client, monkeypatch):
    monkeypatch.setattr(settings, "DEMO_MODE", False)

    def broken(ctx):
        raise RuntimeError("GET https://api.example.com/?key=sk-SECRET123 failed")

    pipeline.register(3, broken)
    run_id = _run_to_research(client)
    message = _events(run_id, 3, EventType.error)[0].payload["message"]
    assert "sk-SECRET123" not in message and "https://" not in message


def test_retry_reruns_only_the_failed_stage_and_continues(client, monkeypatch):
    monkeypatch.setattr(settings, "DEMO_MODE", False)
    calls = {"n": 0}

    def flaky(ctx):
        calls["n"] += 1
        if calls["n"] == 1:
            raise RuntimeError("down")
        return [("research_item", {"competitor": "Acme", "url": "https://acme.test/pricing"})]

    pipeline.register(3, flaky)
    pipeline.register(4, lambda ctx: [])  # stop being the subject of this test: stage 4 yields nothing
    run_id = _run_to_research(client)
    assert _state(client, run_id)["awaiting"] == "retry:3"

    pipeline.retry(run_id)()
    items = _events(run_id, 3, EventType.research_item)
    assert [e.payload["competitor"] for e in items] == ["Acme"]
    assert not items[0].demo_data
    assert calls["n"] == 2


def test_retry_when_nothing_failed_is_a_conflict(client, monkeypatch):
    monkeypatch.setattr(settings, "DEMO_MODE", True)
    run_id = _run_to_research(client)
    with pytest.raises(pipeline.Conflict):
        pipeline.retry(run_id)


# --- Miro: a note that keeps failing is skipped; the rest of the board stays -------------------------

ARCH = Architecture(screens=["Inicio", "Catálogo"], data_model=["Bomba"], integrations=[])


def _nosleep(_s):
    async def done():
        return None

    return done()


def test_miro_skips_a_note_that_still_fails_and_keeps_the_others(monkeypatch):
    monkeypatch.setattr(settings, "MIRO_ACCESS_TOKEN", "test-token")
    counter = {"n": 0}

    def note(request):
        counter["n"] += 1
        if b"Cat\xc3\xa1logo" in request.content:
            return httpx.Response(500, text="Internal error occurred")
        return httpx.Response(200, json={"id": f"n{counter['n']}"})

    async def run():
        board = miro.build_board(ARCH, demo=False, sleep=lambda s: _nosleep(s))
        items = [item async for item in board]
        return board, items

    with respx.mock(assert_all_called=False) as router:
        router.post("https://api.miro.com/v2/boards").mock(return_value=httpx.Response(200, json={"id": "b1"}))
        router.post(url__regex=r".*/frames$").mock(return_value=httpx.Response(200, json={"id": "f"}))
        router.post(url__regex=r".*/sticky_notes$").mock(side_effect=note)
        router.post(url__regex=r".*/connectors$").mock(return_value=httpx.Response(200, json={"id": "c"}))
        board, items = asyncio.run(run())

    titles = [i["title"] for i in items if i["kind"] in ("screen", "data_model")]
    assert titles == ["Inicio", "Bomba"]  # "Catálogo" was skipped, the others kept
    assert board.skipped == ["Catálogo"]
    assert not any(i.get("demo_data") for i in items)
    assert "screen:Catálogo" not in board.ids  # not marked as created, so a retry tries it again
