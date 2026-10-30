"""The 9-stage pipeline: explicit states, 3 human approvals, StageEvents (IDEA.md §5).

Each stage runs through a registry. A stage module exposes `run_stage(ctx) -> Iterable[(event_type, payload)]`
and may call `ctx.add_cost(usd)`. A missing module, an exception or a payload that fails its schema falls
back to `app/fixtures/demo/run.jsonl`, labeled `demo_data: true`, so a run always finishes.
"""
from __future__ import annotations

import importlib
import json
import logging
import os
import time
from collections.abc import Callable, Iterable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from app.config import settings
from app.schemas import (
    PAYLOAD_MODELS,
    STAGES,
    Approval,
    ApprovalState,
    EventType,
    Mode,
    Project,
    Run,
    RunStatus,
    StageEvent,
)
from app.services import memory, pitch, store

log = logging.getLogger(__name__)

FIXTURE = Path(__file__).resolve().parent.parent / "fixtures" / "demo" / "run.jsonl"
# The human approves after these stages: spec, backlog, quality report.
GATES = {4: 1, 6: 2, 8: 3}
# Module (under app.services) that implements each stage; absent modules fall back to the fixture.
# `stages` connects every stage, the intake included, to its real service.
STAGE_MODULES = dict.fromkeys(range(1, 10), "stages")
# Events the pipeline emits itself, so they are dropped when replaying the fixture.
OWN_EVENTS = {EventType.stage_started, EventType.stage_done, EventType.approval_required, EventType.approval_given}
# Stages that run for real even in DEMO_MODE: they need no key or network (the recorded SpeedHack app is
# copied for the run and checked locally), so a judge without keys sees the prototype and real checks.
DEMO_LIVE_STAGES = {7, 8}

Produced = list[tuple[float, EventType, dict[str, Any]]]  # (delay before, type, payload)


class Conflict(Exception):
    """The run is not waiting for what the caller sent."""


class StageFailed(Exception):
    """A provider failed in a real run: tell the user, keep the run on this stage, never replay a recording."""

    def __init__(self, stage: int, message: str) -> None:
        super().__init__(message)
        self.stage = stage
        self.message = message


# Who to blame, in the user's words, when a stage fails in a real run.
PROVIDER_NAMES = {
    1: "Claude", 2: "Claude", 3: "Tavily o Firecrawl", 4: "Claude", 5: "Miro",
    6: "Linear", 7: "el generador del prototipo", 8: "los chequeos de calidad", 9: "Claude",
}


def _failure_message(stage: int) -> str:
    # Never the exception text: it can carry URLs, ids or keys. The detail goes to the server log.
    return (
        f"La etapa «{STAGES[stage]}» no se pudo completar: {PROVIDER_NAMES[stage]} no respondió. "
        "Revisa la llave o el estado del servicio y pulsa «Reintentar»."
    )


@dataclass
class StageContext:
    run: Run
    project: Project
    stage: int
    comment: str | None = None  # why the human sent the run back to this stage
    spec: dict[str, Any] | None = None
    answers: list[str] = field(default_factory=list)
    externals: dict[str, str] = field(default_factory=dict)  # IDs already created for this stage
    cost: float = 0.0

    def add_cost(self, usd: float) -> None:
        self.cost += usd


StageFn = Callable[[StageContext], Iterable[tuple[Any, dict[str, Any]]]]
REGISTRY: dict[int, StageFn] = {}


def register(stage: int, fn: StageFn) -> None:
    REGISTRY[stage] = fn


def _provider(stage: int) -> StageFn | None:
    if stage in REGISTRY:
        return REGISTRY[stage]
    try:
        return importlib.import_module(f"app.services.{STAGE_MODULES[stage]}").run_stage
    except (KeyError, ImportError, AttributeError):
        return None


def _speed() -> float:
    """DEMO_SPEED divides the recorded delays; 0 replays instantly (tests)."""
    return float(os.environ.get("DEMO_SPEED", "2"))


def _fixture(stage: int) -> Produced:
    out: Produced = []
    last = 0.0
    for line in FIXTURE.read_text().splitlines():
        d = json.loads(line)
        if d["stage"] != stage:
            continue
        etype = EventType(d["type"])
        if etype not in OWN_EVENTS:
            out.append((max(0.0, d["ts"] - last), etype, d["payload"]))
        last = d["ts"]
    return out


def _validated(stage: int, raw: Iterable[tuple[Any, dict[str, Any]]]) -> Produced:
    out: Produced = []
    for etype, payload in raw:
        etype = EventType(etype)
        model = PAYLOAD_MODELS.get(etype)
        if model is not None:
            model.model_validate(payload)
        out.append((0.0, etype, dict(payload)))
    return out


def _emit(run_id: str, stage: int, etype: EventType, payload: dict[str, Any], demo: bool) -> None:
    store.add_event(
        StageEvent(run_id=run_id, stage=stage, type=etype, payload=payload, ts=store.elapsed(run_id), demo_data=demo)
    )


def _produce(ctx: StageContext) -> tuple[Produced, bool]:
    """Events for the stage and whether they are demo data."""
    live = not settings.DEMO_MODE or ctx.stage in DEMO_LIVE_STAGES
    fn = _provider(ctx.stage) if live else None
    if fn is not None:
        try:
            events = _validated(ctx.stage, fn(ctx))
            # A service that answered from its own recorded data (no key, plan B) is still demo data.
            return events, any(payload.get("demo_data") for _, _, payload in events)
        except Exception as exc:
            if not settings.DEMO_MODE:
                # A real run must never show another project's recording as if it were its own.
                log.exception("stage %s failed in a real run", ctx.stage)
                raise StageFailed(ctx.stage, _failure_message(ctx.stage)) from exc
            log.exception("stage %s failed, falling back to the recorded run", ctx.stage)
        finally:
            # Money spent before a failure is still spent: record it whether or not the stage succeeded.
            if ctx.cost:
                store.add_cost(ctx.run.run_id, STAGES[ctx.stage], ctx.cost)
    return _fixture(ctx.stage), True


def _remember(run_id: str, kind: str, text: str, source: str) -> None:
    """Feed the pitch room's source-checked memory; a memory failure never stops the run."""
    try:
        memory.remember(run_id, kind, text, source)
    except Exception:
        log.exception("memory.remember failed for run %s", run_id)


def _remember_spec(run_id: str, spec: dict[str, Any]) -> None:
    source = f"spec:v{spec['version']}"
    _remember(run_id, "spec", json.dumps(spec, ensure_ascii=False), source)
    # Readable passages so Q&A can quote the spec; the JSON above stays the source for the deck.
    _remember(run_id, "spec_note", f"Problema: {spec['problem']}", source)
    if spec.get("users"):
        _remember(run_id, "spec_note", "Usuarios: " + "; ".join(spec["users"]), source)
    for feature in spec.get("mvp_features", []):
        _remember(run_id, "spec_note", f"Funcionalidad del MVP: {feature}", source)


def _remember_research_note(run_id: str, item: dict[str, Any]) -> None:
    # Spanish wording so judge questions ("competidores", "precio", "competencia") match the passage.
    features = item.get("features") or []
    if isinstance(features, list):
        features = ", ".join(str(f) for f in features)
    text = (
        f"Competidores y competencia: {item.get('competitor', 'sin nombre')}. "
        f"Precio: {item.get('pricing') or 'sin precio publicado'}. "
        f"Funciones: {features or 'sin datos'}."
    )
    _remember(run_id, "research_note", text, item["url"])


def _deck_from_memory(run_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    """A pitch with no slides (the recorded fixture) is replaced by one built from this run's memory."""
    try:
        deck = pitch.deck(run_id)
    except Exception:
        log.exception("pitch deck from memory failed for run %s", run_id)
        return payload
    return {**payload, **deck.model_dump(mode="json")} if deck.slides else payload


def _record(run_id: str, stage: int, etype: EventType, payload: dict[str, Any]) -> dict[str, Any]:
    """Persist what later stages and the spec of record need; returns the payload to emit."""
    if etype is EventType.spec_ready:
        payload = {**payload, "version": store.add_spec(run_id, payload)}
        _remember_spec(run_id, payload)
    elif etype is EventType.research_item:
        _remember(run_id, "research", json.dumps(payload, ensure_ascii=False), payload["url"])
        _remember_research_note(run_id, payload)
    elif etype is EventType.pitch_ready and not payload.get("slides"):
        payload = _deck_from_memory(run_id, payload)
    elif etype is EventType.miro_item and payload.get("miro_id"):
        store.set_external(run_id, stage, f"miro:{payload['title']}", payload["miro_id"])
    elif etype is EventType.linear_issue and payload.get("linear_id"):
        store.set_external(run_id, stage, f"linear:{payload['external_id']}", payload["linear_id"])
    return payload


def _run_stage(run_id: str, stage: int, comment: str | None) -> None:
    run, speed = store.get_run(run_id), _speed()
    ctx = StageContext(
        run=run,  # type: ignore[arg-type]
        project=store.get_project(run.project_id),  # type: ignore[union-attr]
        stage=stage,
        comment=comment,
        spec=store.get_spec(run_id),
        answers=store.get_answers(run_id),
        externals=store.get_externals(run_id, stage),
    )
    store.set_state(run_id, stage=stage, status=RunStatus.running)
    events, demo = _produce(ctx)
    if demo:
        store.mark_demo(run_id)
    name = STAGES[stage]
    _emit(run_id, stage, EventType.stage_started, {"name": name}, demo)
    for delay, etype, payload in events:
        if speed > 0:
            time.sleep(delay / speed)
        _emit(run_id, stage, etype, _record(run_id, stage, etype, payload), demo)
    _emit(run_id, stage, EventType.stage_done, {"name": name}, demo)


def _advance(run_id: str, first: int, comment: str | None = None) -> None:
    """Run stages from `first` until the next human gate (questions or approval) or the end."""
    stage = first
    try:
        while stage <= 9:
            _run_stage(run_id, stage, comment)
            comment = None
            if stage == 2:
                store.set_state(run_id, status=RunStatus.pending, awaiting="answers")
                return
            if stage in GATES:
                _emit(run_id, stage, EventType.approval_required, {"approval": GATES[stage]}, store.get_run(run_id).demo_data)  # type: ignore[union-attr]
                store.set_state(run_id, status=RunStatus.awaiting_approval, awaiting=f"approval:{GATES[stage]}")
                return
            stage += 1
        store.set_state(run_id, status=RunStatus.done)
    except StageFailed as failed:
        _emit(run_id, failed.stage, EventType.error, {"message": failed.message, "retry": True}, False)
        store.set_state(run_id, stage=failed.stage, status=RunStatus.failed, awaiting=f"retry:{failed.stage}")
    except Exception as exc:
        log.exception("run %s failed", run_id)
        _emit(run_id, stage, EventType.error, {"message": str(exc)}, True)
        store.set_state(run_id, status=RunStatus.failed)


def retry(run_id: str) -> Callable[[], None]:
    """Run again the stage that failed. Ids it already created in Miro or Linear are reused, not duplicated."""
    awaiting = store.get_awaiting(run_id) or ""
    stage = int(awaiting.removeprefix("retry:")) if awaiting.startswith("retry:") else 0
    if not stage or not store.claim(run_id, awaiting):
        raise Conflict("the run has no failed stage to retry")
    return lambda: _advance(run_id, stage)


def create(mode: Mode, idea: str, stack_prefs: list[str] | None = None) -> Run:
    """Create the project and run. Call `start` (a background task) to execute stages 1-2."""
    _, run = store.create_run(mode, idea, stack_prefs or [], settings.DEMO_MODE)
    return run


def start(run_id: str) -> None:
    if store.claim(run_id, "start"):
        _advance(run_id, 1)


def answer(run_id: str, answers: list[str]) -> Callable[[], None]:
    """Record the answers now; the returned function runs the rest of the stages (a background task)."""
    if not store.claim(run_id, "answers"):
        raise Conflict("the run is not waiting for answers")
    store.add_answers(run_id, answers)
    return lambda: _advance(run_id, 3)


def decide(run_id: str, number: int, approved: bool, comment: str | None) -> Callable[[], None]:
    """Record approval `number` now. Approved: the returned function continues. Rejected: it goes back one stage."""
    if number not in GATES.values():
        raise ValueError(f"approval must be 1, 2 or 3, got {number}")
    if not store.claim(run_id, f"approval:{number}"):
        raise Conflict(f"the run is not waiting for approval {number}")
    run = store.get_run(run_id)
    assert run is not None
    gate_stage = next(s for s, n in GATES.items() if n == number)
    approvals = list(run.approvals)
    if approved:
        approvals[number - 1] = Approval(number=number, state=ApprovalState.approved, decided_by="human")
        store.set_state(run_id, approvals=approvals)
        _emit(run_id, gate_stage, EventType.approval_given, {"approval": number, "by": "human"}, run.demo_data)
        return lambda: _advance(run_id, gate_stage + 1)
    approvals[number - 1] = Approval(number=number)  # back to pending for the next attempt
    store.set_state(run_id, approvals=approvals)
    _emit(run_id, gate_stage, EventType.approval_rejected, {"approval": number, "comment": comment or ""}, run.demo_data)
    return lambda: _advance(run_id, gate_stage - 1, comment)
