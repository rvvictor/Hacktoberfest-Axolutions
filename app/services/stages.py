"""Stage adapters: connect each pipeline stage to its real service (IDEA.md §5, §7).

`pipeline` imports `run_stage(ctx)` for stages 1-9. Each adapter reads what earlier stages produced
from the run's events (the latest attempt only, so a rejection never doubles anything) and returns
`(event_type, payload)` pairs. The services fall back to their own recorded data when a key is
missing; those payloads carry `demo_data: true` and the pipeline keeps the stage labeled as demo.
Raising makes the pipeline replay the labeled fixture for the stage.
"""
from __future__ import annotations

import asyncio
import logging
from collections.abc import AsyncIterable, Iterable
from concurrent.futures import ThreadPoolExecutor
from typing import TYPE_CHECKING, Any

import httpx

from app.config import settings
from app.schemas import (
    Architecture,
    BacklogItem,
    EventType,
    ResearchItem,
    Spec,
    StageEvent,
)
from app.services import generator, linear, llm, miro, quality, research, store

if TYPE_CHECKING:
    from app.services.pipeline import StageContext

log = logging.getLogger(__name__)
Events = list[tuple[str, dict[str, Any]]]
REJECTION_NOTE = "Cambio pedido por la persona que revisó"
# BoardRun's own ids (board, frames, notes, connectors) live in `externals` under this prefix, so a
# rerun of stage 5 reuses the same Miro board instead of creating a new one.
BOARD_IDS = "boardrun:"
GROUPS = {"screen": "screens", "data_model": "data_model", "integration": "integrations"}


class StageUnavailable(Exception):
    """No honest real output for this stage: the pipeline replays the labeled fixture."""


# --- reading earlier stages -------------------------------------------------------------------


def _latest(run_id: str, stage: int) -> list[StageEvent]:
    """Events of the latest attempt of `stage` (everything after its last stage_started)."""
    events = [e for _, e in store.list_events(run_id) if e.stage == stage]
    starts = [i for i, e in enumerate(events) if e.type is EventType.stage_started]
    return events[starts[-1] + 1 :] if starts else events


def _payloads(run_id: str, stage: int, etype: EventType) -> list[dict[str, Any]]:
    return [e.payload for e in _latest(run_id, stage) if e.type is etype]


def _research(run_id: str) -> list[ResearchItem]:
    return [ResearchItem.model_validate(p) for p in _payloads(run_id, 3, EventType.research_item)]


def _answers(ctx: StageContext) -> dict[str, str]:
    questions = [p.get("text", "") for p in _payloads(ctx.run.run_id, 2, EventType.question)]
    return {q: a for q, a in zip(questions, ctx.answers, strict=False) if q}


def _rejection(run_id: str, number: int) -> str | None:
    """The comment of approval `number` if its latest decision was a rejection."""
    last = None
    for _, e in store.list_events(run_id):
        if e.payload.get("approval") == number and e.type in (EventType.approval_given, EventType.approval_rejected):
            last = e
    if last is not None and last.type is EventType.approval_rejected:
        return last.payload.get("comment") or None
    return None


def _spec(ctx: StageContext) -> Spec:
    if not ctx.spec:
        raise StageUnavailable("no spec of record yet")
    return Spec.model_validate(ctx.spec)


def _architecture(run_id: str) -> Architecture:
    """Rebuild the architecture from the Miro items of the latest stage-5 attempt."""
    groups: dict[str, list[str]] = {name: [] for name in GROUPS.values()}
    for p in _payloads(run_id, 5, EventType.miro_item):
        name = GROUPS.get(p.get("kind", ""))
        if name and p.get("title") not in groups[name]:
            groups[name].append(p["title"])
    if not any(groups.values()):
        raise StageUnavailable("no architecture items from stage 5")
    return Architecture(**groups)


def _collect(items: AsyncIterable[dict[str, Any]]) -> list[dict[str, Any]]:
    """Drain an async iterator from this (worker) thread, even if an event loop is running here."""

    async def drain() -> list[dict[str, Any]]:
        return [item async for item in items]

    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(drain())
    with ThreadPoolExecutor(max_workers=1) as pool:
        return pool.submit(asyncio.run, drain()).result()


async def _no_wait(_seconds: float) -> None:
    """The pipeline paces the recorded replay itself; the Miro service must not sleep on top of it."""


async def _backoff(seconds: float) -> None:
    """Live Miro calls: honour the 429 Retry-After wait."""
    await asyncio.sleep(seconds)


# --- stages -----------------------------------------------------------------------------------


def _intake(ctx: StageContext) -> Events:
    return []  # the idea is already stored; nothing to call


def _clarify(ctx: StageContext) -> Events:
    mode = ctx.project.mode
    # `clarify` returns bare strings, so whether they came from the recording is asked of the service.
    demo = llm._demo()
    questions = llm.clarify(ctx.project.idea, mode)
    return [("question", {"text": q, "mode": mode.value, "demo_data": demo}) for q in questions]


def _research_stage(ctx: StageContext) -> Events:
    draft = " ".join([ctx.project.idea, *ctx.answers])
    items = research.research(
        draft,
        ctx.project.mode.value,
        data_dir=settings.DATA_DIR,
        api_key=settings.TAVILY_API_KEY,
        firecrawl_key=settings.FIRECRAWL_API_KEY,
        stack=ctx.project.stack_prefs,
    )
    return [("research_item", item.model_dump(mode="json")) for item in items]


def _spec_stage(ctx: StageContext) -> Events:
    answers = _answers(ctx)
    comment = _rejection(ctx.run.run_id, 1)
    if comment:
        answers[REJECTION_NOTE] = comment
    version = (ctx.spec or {}).get("version", 0) + 1
    spec = llm.build_spec(ctx.project.idea, ctx.project.mode, answers, _research(ctx.run.run_id), version)
    return [("spec_ready", spec.model_dump(mode="json"))]


def _architecture_stage(ctx: StageContext) -> Events:
    spec = _spec(ctx)
    comment = _rejection(ctx.run.run_id, 2)
    if comment:  # build_architecture only reads the spec: carry the request as an assumption
        spec = spec.model_copy(update={"assumptions": [*spec.assumptions, f"{REJECTION_NOTE}: {comment}"]})
    architecture = llm.build_architecture(spec)
    ids = {k[len(BOARD_IDS) :]: v for k, v in ctx.externals.items() if k.startswith(BOARD_IDS)}
    demo = (
        settings.DEMO_MODE or not settings.MIRO_ACCESS_TOKEN or architecture.demo_data or spec.demo_data
    )
    # In demo the pipeline paces the replay itself; live, BoardRun also sleeps for Miro's 429
    # Retry-After backoff, which must really wait.
    board = miro.build_board(architecture, demo=demo, ids=ids, sleep=_no_wait if demo else _backoff)
    try:
        items = _collect(board)
    finally:
        if not demo:
            for key, value in board.ids.items():
                store.set_external(ctx.run.run_id, ctx.stage, BOARD_IDS + key, value)
    items = _already_on_board(ctx.run.run_id, architecture, board.ids, items) + items
    return [("miro_item", {**item, "demo_data": item.get("demo_data", demo)}) for item in items]


def _already_on_board(
    run_id: str, architecture: Architecture, ids: dict[str, str], created: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    """Items an earlier attempt put on the board that are still in the architecture.

    BoardRun only yields what it creates, so on a rerun the existing frames, notes and connectors
    would vanish from the live view and from the architecture stage 6 rebuilds.
    """
    on_board = set(ids.values()) - {i.get("miro_id") for i in created}
    earlier: dict[str, dict[str, Any]] = {}
    for _, e in store.list_events(run_id):
        miro_id = e.payload.get("miro_id")
        if e.stage == 5 and e.type is EventType.miro_item and miro_id in on_board:
            earlier[miro_id] = e.payload
    current = {kind: set(getattr(architecture, name)) for kind, name in GROUPS.items()}
    # A note created by an attempt that failed before emitting it has an id but no event yet:
    # BoardRun keys notes as "<kind>:<text>", so it can still be shown (at the frame origin).
    for key, miro_id in ids.items():
        kind, _, title = key.partition(":")
        if miro_id in on_board and miro_id not in earlier and title in current.get(kind, ()):
            earlier[miro_id] = {"kind": kind, "title": title, "miro_id": miro_id, "x": 0, "y": 0}
    return [
        {k: v for k, v in p.items() if k != "demo_data"}
        for p in earlier.values()
        if p.get("kind") not in current or p.get("title") in current[p["kind"]]
    ]


def _backlog_stage(ctx: StageContext) -> Events:
    spec = _spec(ctx)
    items: list[BacklogItem] = llm.build_backlog(spec, _architecture(ctx.run.run_id))
    if settings.DEMO_MODE or any(i.demo_data for i in items):
        return [("linear_issue", {**i.model_dump(mode="json"), "demo_data": True}) for i in items]
    # Linear dedupes by the external_id marker, so a rerun reuses the issues already created.
    return [("linear_issue", e.payload) for e in linear.create_backlog(items, ctx.run.run_id)]


def _prototype_stage(ctx: StageContext) -> Events:
    spec = _spec(ctx)
    backlog = [BacklogItem.model_validate(p) for p in _payloads(ctx.run.run_id, 6, EventType.linear_issue)]
    try:
        # SpeedHack builds the app itself; Lovable stays as the link to keep building it there.
        return [("prototype_ready", generator.SpeedHackGenerator(ctx.run.run_id, ctx.comment).generate(spec, backlog).model_dump(mode="json"))]
    except (llm.LLMError, httpx.HTTPError, OSError, ValueError):
        log.exception("SpeedHack generation failed for %s; falling back to Lovable", ctx.run.run_id)
    prototype = generator.LovableGenerator().generate(spec, backlog)
    if settings.LOVABLE_PREBUILT_URL:
        # The delivery view previews `url` in a frame; a Build-with-URL link is a prompt page, not an
        # app. Preview the prebuilt app and keep this run's link to build its own; the prebuilt app
        # was not generated from this run, so the item is labeled demo.
        prototype = prototype.model_copy(update={"url": settings.LOVABLE_PREBUILT_URL, "demo_data": True})
    return [("prototype_ready", prototype.model_dump(mode="json"))]


def _quality_stage(ctx: StageContext) -> Events:
    # Only the app SpeedHack generated is here to check. A Lovable or prebuilt app has no local copy:
    # reporting checks we did not run would be invented, so the stage keeps the labeled recorded report.
    made = _payloads(ctx.run.run_id, 7, EventType.prototype_ready)
    path = generator.prototype_path(ctx.run.run_id)
    if not made or made[-1].get("generator") != "speedhack" or not path.exists():
        raise StageUnavailable("no local copy of the generated app to check")
    demo = bool(made[-1].get("demo_data"))
    report = quality.check_app(path, demo_data=demo)
    if not report.checks:
        raise StageUnavailable(f"no check could run here ({report.details})")
    return [("quality_check", {**c.model_dump(mode="json"), "demo_data": demo}) for c in report.checks]


def _pitch_stage(ctx: StageContext) -> Events:
    deck = llm.build_deck(_spec(ctx), _research(ctx.run.run_id))
    return [("pitch_ready", deck.model_dump(mode="json"))]


ADAPTERS = {
    1: _intake,
    2: _clarify,
    3: _research_stage,
    4: _spec_stage,
    5: _architecture_stage,
    6: _backlog_stage,
    7: _prototype_stage,
    8: _quality_stage,
    9: _pitch_stage,
}


def run_stage(ctx: StageContext) -> Iterable[tuple[str, dict[str, Any]]]:
    return ADAPTERS[ctx.stage](ctx)
