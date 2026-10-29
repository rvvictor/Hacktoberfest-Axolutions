import asyncio
from typing import ClassVar

import pytest
from fastapi.testclient import TestClient

from app.config import settings
from app.main import app
from app.schemas import (
    Architecture,
    BacklogItem,
    EventType,
    Pitch,
    ResearchItem,
    Spec,
    StageEvent,
)
from app.services import pipeline, stages, store

QUESTIONS = ["¿Varias empresas?", "¿Qué roles?", "¿Qué alertas?"]


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "DATA_DIR", tmp_path)
    monkeypatch.setattr(settings, "DEMO_MODE", False)
    monkeypatch.setenv("DEMO_SPEED", "0")
    monkeypatch.setattr(pipeline, "REGISTRY", {})
    return TestClient(app)


class FakeBoard:
    """Stands in for miro.BoardRun: async-iterable items, records the ids it was given."""

    calls: ClassVar[list[dict]] = []

    def __init__(self, architecture, *, demo, ids, sleep):
        self.ids = dict(ids)
        FakeBoard.calls.append({"architecture": architecture, "demo": demo, "ids": dict(ids)})

    def __aiter__(self):
        return self._items()

    async def _items(self):
        self.ids.setdefault("board", "b1")
        for n, (kind, title) in enumerate([("screen", "Login"), ("data_model", "Gasto"), ("integration", "Supabase")]):
            self.ids[f"{kind}:{title}"] = f"m{n}"
            yield {"kind": kind, "title": title, "miro_id": f"m{n}", "x": n, "y": 0}


@pytest.fixture
def live_services(monkeypatch):
    """Real-looking answers (no demo_data) from every service, recording what each one received."""
    seen: dict = {"spec_answers": [], "arch_assumptions": [], "backlog_arch": None}
    FakeBoard.calls = []
    monkeypatch.setattr(stages.settings, "MIRO_ACCESS_TOKEN", "token")
    monkeypatch.setattr(stages.llm, "_demo", lambda: False)  # as if the LLM key were set
    monkeypatch.setattr(stages.llm, "clarify", lambda idea, mode: QUESTIONS)
    research_calls = []

    def fake_research(draft, mode, **kw):
        research_calls.append(draft)
        return [ResearchItem(competitor="Acme", features=["alertas"], url="https://acme.test/pricing")]

    monkeypatch.setattr(stages.research, "research", fake_research)

    def fake_spec(idea, mode, answers, research, version=1):
        seen["spec_answers"].append(answers)
        assert [r.url for r in research] == ["https://acme.test/pricing"]  # latest attempt only
        return Spec(version=version, problem=idea, users=["Finanzas"], mvp_features=["Captura"], sources=["https://acme.test/pricing"])

    monkeypatch.setattr(stages.llm, "build_spec", fake_spec)

    def fake_arch(spec):
        seen["arch_assumptions"].append(list(spec.assumptions))
        return Architecture(screens=["Login"], data_model=["Gasto"], integrations=["Supabase"])

    monkeypatch.setattr(stages.llm, "build_architecture", fake_arch)
    monkeypatch.setattr(stages.miro, "build_board", FakeBoard)

    def fake_backlog(spec, architecture):
        seen["backlog_arch"] = architecture
        return [BacklogItem(epic="Gastos", title="Captura", acceptance=["Monto obligatorio"], external_id="e1")]

    monkeypatch.setattr(stages.llm, "build_backlog", fake_backlog)

    def fake_linear(items, run_id):
        for i in items:
            payload = {**i.model_dump(mode="json"), "linear_id": "GAS-1", "url": "https://linear.app/x/GAS-1"}
            yield StageEvent(run_id=run_id, stage=6, type=EventType.linear_issue, payload=payload, ts=0)

    monkeypatch.setattr(stages.linear, "create_backlog", fake_linear)
    app = "<!DOCTYPE html><html><body><h1>Captura</h1><script>let monto = 0;</script></body></html>"
    monkeypatch.setattr(stages.llm, "build_app", lambda system, user, validate: validate(app))
    monkeypatch.setattr(
        stages.llm, "build_deck", lambda spec, research: Pitch(slides=[{"title": "SpeedHack", "bullets": ["b"], "sources": []}])
    )
    seen["research_calls"] = research_calls
    return seen


def _start(client):
    r = client.post("/api/projects", json={"mode": "dev", "idea": "SaaS de gastos"})
    assert r.status_code == 201
    run_id = r.json()["run_id"]
    assert client.post(f"/api/runs/{run_id}/answers", json={"answers": ["sí", "admin", "correo"]}).status_code == 200
    return run_id


def _approve(client, run_id, n, approved=True, comment=None):
    return client.post(f"/api/runs/{run_id}/approvals/{n}", json={"approved": approved, "comment": comment})


def _demo_by_stage(run_id):
    by_stage: dict[int, set] = {}
    for _, e in store.list_events(run_id):
        if e.type not in (EventType.stage_started, EventType.stage_done):
            continue
        by_stage.setdefault(e.stage, set()).add(e.demo_data)
    return {s: v == {True} for s, v in by_stage.items()}


def test_live_run_calls_the_services_and_no_stage_stays_demo(client, live_services):
    run_id = _start(client)
    for n in (1, 2, 3):
        assert _approve(client, run_id, n).status_code == 200
    state = client.get(f"/api/runs/{run_id}").json()
    assert state["status"] == "done"
    demo = _demo_by_stage(run_id)
    assert [s for s, d in demo.items() if d] == []  # quality checks the app SpeedHack generated
    # what each stage received from the earlier ones
    assert live_services["spec_answers"][0] == dict(zip(QUESTIONS, ["sí", "admin", "correo"], strict=True))
    assert live_services["backlog_arch"] == Architecture(screens=["Login"], data_model=["Gasto"], integrations=["Supabase"])
    issue = next(e for _, e in store.list_events(run_id) if e.type is EventType.linear_issue)
    assert issue.payload["linear_id"] == "GAS-1" and not issue.demo_data
    proto = next(e for _, e in store.list_events(run_id) if e.type is EventType.prototype_ready)
    assert proto.payload["generator"] == "speedhack" and proto.payload["url"] == f"/api/prototypes/{run_id}/"
    assert proto.payload["build_url"].startswith("https://lovable.dev/")
    checks = [e.payload for _, e in store.list_events(run_id) if e.type is EventType.quality_check]
    assert {"lint", "secrets"} <= {c["name"] for c in checks} and all(c["passed"] for c in checks)


def test_rejections_carry_the_comment_and_reuse_the_miro_board(client, live_services):
    run_id = _start(client)
    assert _approve(client, run_id, 1, approved=False, comment="Agrega roles de auditor").status_code == 200
    assert live_services["spec_answers"][-1][stages.REJECTION_NOTE] == "Agrega roles de auditor"
    assert len(live_services["research_calls"]) == 2  # research ran again; the spec saw only the latest
    assert _approve(client, run_id, 1).status_code == 200
    assert _approve(client, run_id, 2, approved=False, comment="Separa notificaciones").status_code == 200
    assert live_services["arch_assumptions"][-1][-1].endswith("Separa notificaciones")
    first, second = FakeBoard.calls[0], FakeBoard.calls[-1]
    assert first["ids"] == {} and second["ids"]["board"] == "b1"  # same board, no duplicate in Miro


def test_services_falling_back_to_their_recordings_keep_the_run_labeled_demo(client):
    """DEMO_MODE off but no keys (conftest blanks them): every service answers from its recording."""
    run_id = _start(client)
    for n in (1, 2, 3):
        _approve(client, run_id, n)
    assert client.get(f"/api/runs/{run_id}").json()["status"] == "done"
    demo = _demo_by_stage(run_id)
    assert demo.pop(1) is False  # the intake calls nothing, so there is nothing recorded to label
    assert all(demo.values()), demo
    assert store.get_run(run_id).demo_data


def test_collect_works_inside_a_running_event_loop():
    async def items():
        yield {"a": 1}

    async def inside_loop():
        return stages._collect(items())

    assert asyncio.run(inside_loop()) == [{"a": 1}]


def test_rerun_with_the_real_board_still_shows_every_item_and_creates_one_board(client, live_services, monkeypatch):
    """The real BoardRun skips items already on the board; the adapter must still emit all of them."""
    import itertools
    import re

    import httpx
    import respx

    from app.services import miro as miro_service

    # live_services swapped build_board for FakeBoard: go back to the real BoardRun class
    monkeypatch.setattr(stages.miro, "build_board", lambda arch, **kw: miro_service.BoardRun(arch, **kw))
    ids = itertools.count(1)
    with respx.mock(assert_all_mocked=True) as router:
        boards = router.post("https://api.miro.com/v2/boards").mock(
            side_effect=lambda request: httpx.Response(201, json={"id": "board-1"})
        )
        router.post(url__regex=re.compile(r"https://api\.miro\.com/v2/boards/board-1/.*")).mock(
            side_effect=lambda request: httpx.Response(201, json={"id": f"item-{next(ids)}"})
        )
        run_id = _start(client)
        assert _approve(client, run_id, 1).status_code == 200
        assert _approve(client, run_id, 2, approved=False, comment="Igual, revisa de nuevo").status_code == 200

    def notes(attempt_events):
        return sorted(p["title"] for p in attempt_events if p.get("kind") in ("screen", "data_model", "integration"))

    latest = stages._payloads(run_id, 5, EventType.miro_item)
    assert notes(latest) == ["Gasto", "Login", "Supabase"]  # nothing new to create, all still shown
    assert boards.call_count == 1  # the rerun reused the board
    assert live_services["backlog_arch"] == Architecture(screens=["Login"], data_model=["Gasto"], integrations=["Supabase"])


def test_prototype_previews_the_prebuilt_app_and_keeps_this_runs_build_link(client, live_services, monkeypatch):
    monkeypatch.setattr(stages.settings, "LOVABLE_PREBUILT_URL", "https://prebuilt.lovable.app")

    def generation_fails(system, user, validate):
        raise stages.llm.LLMOutputError("app: invalid output after retry")

    monkeypatch.setattr(stages.llm, "build_app", generation_fails)  # the prebuilt app is only the fallback
    run_id = _start(client)
    _approve(client, run_id, 1)
    _approve(client, run_id, 2)
    proto = next(e for _, e in store.list_events(run_id) if e.type is EventType.prototype_ready)
    assert proto.payload["url"] == "https://prebuilt.lovable.app"
    assert proto.payload["build_url"].startswith("https://lovable.dev/")
    assert proto.demo_data  # not generated from this run's spec


def _real_board_with_mocked_miro(monkeypatch, router, ids, first_note_status=None):
    import re

    import httpx

    from app.services import miro as miro_service

    monkeypatch.setattr(stages.miro, "build_board", lambda arch, **kw: miro_service.BoardRun(arch, **kw))
    router.post("https://api.miro.com/v2/boards").mock(return_value=httpx.Response(201, json={"id": "board-1"}))
    responses = iter(first_note_status or [])

    def reply(request):
        status = next(responses, None)
        if status == 429:
            return httpx.Response(429, headers={"Retry-After": "3"})
        if status == "boom":
            raise httpx.ConnectError("miro down")
        return httpx.Response(201, json={"id": f"item-{next(ids)}"})

    router.post(url__regex=re.compile(r"https://api\.miro\.com/v2/boards/board-1/.*")).mock(side_effect=reply)


def test_live_miro_rate_limit_really_waits_and_the_stage_stays_real(client, live_services, monkeypatch):
    import itertools

    import respx

    waits = []

    async def record_wait(seconds):
        waits.append(seconds)

    monkeypatch.setattr(stages, "_backoff", record_wait)
    with respx.mock() as router:
        _real_board_with_mocked_miro(monkeypatch, router, itertools.count(1), first_note_status=[429])
        run_id = _start(client)
        _approve(client, run_id, 1)
    assert waits == [3.0]  # Retry-After honoured instead of retrying in a tight loop
    items = stages._payloads(run_id, 5, EventType.miro_item)
    assert items and not any(p.get("demo_data") for p in items)


def test_items_created_before_a_failure_show_up_on_the_rerun(client, live_services, monkeypatch):
    import itertools

    import respx

    ids = itertools.count(1)
    # first attempt: frames (3) + first note created, then Miro fails on the second note
    with respx.mock() as router:
        _real_board_with_mocked_miro(monkeypatch, router, ids, first_note_status=[None, None, None, None, "boom"])
        run_id = _start(client)
        _approve(client, run_id, 1)
    assert store.get_externals(run_id, 5)  # the ids created before the failure were kept
    with respx.mock(assert_all_called=False) as router:  # the board exists: no new board is created
        _real_board_with_mocked_miro(monkeypatch, router, ids)
        _approve(client, run_id, 2, approved=False, comment="otra vez")
        assert not router.routes[0].called
    titles = sorted(
        p["title"] for p in stages._payloads(run_id, 5, EventType.miro_item) if p["kind"] in stages.GROUPS
    )
    assert titles == ["Gasto", "Login", "Supabase"]
