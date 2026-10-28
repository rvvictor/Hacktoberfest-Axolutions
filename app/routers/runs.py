import asyncio
from typing import Any

from fastapi import APIRouter, BackgroundTasks, Header, HTTPException, Query
from pydantic import BaseModel, Field
from sse_starlette.sse import EventSourceResponse

from app.schemas import Mode, RunStatus
from app.services import pipeline, store

router = APIRouter(prefix="/api")

POLL_SECONDS = 0.1


class ProjectIn(BaseModel):
    mode: Mode
    idea: str = Field(min_length=1)
    stack_prefs: list[str] = Field(default_factory=list)


class AnswersIn(BaseModel):
    answers: list[str] = Field(min_length=1)


class ApprovalIn(BaseModel):
    approved: bool
    comment: str | None = None


def _state(run_id: str) -> dict[str, Any]:
    run = store.get_run(run_id)
    if run is None:
        raise HTTPException(404, f"run {run_id} not found")
    spec = store.get_spec(run_id)
    return {**run.model_dump(mode="json"), "awaiting": store.get_awaiting(run_id), "spec": spec}


@router.post("/projects", status_code=201)
def create_project(body: ProjectIn, background: BackgroundTasks) -> dict[str, Any]:
    run = pipeline.create(body.mode, body.idea.strip(), body.stack_prefs)
    background.add_task(pipeline.start, run.run_id)
    return run.model_dump(mode="json")


@router.get("/runs/{run_id}")
def get_run(run_id: str) -> dict[str, Any]:
    return _state(run_id)


@router.post("/runs/{run_id}/answers")
def post_answers(run_id: str, body: AnswersIn, background: BackgroundTasks) -> dict[str, Any]:
    _state(run_id)
    try:
        background.add_task(pipeline.answer(run_id, body.answers))
    except pipeline.Conflict as exc:
        raise HTTPException(409, str(exc))
    return {"run_id": run_id, "accepted": True}


@router.post("/runs/{run_id}/approvals/{number}")
def post_approval(run_id: str, number: int, body: ApprovalIn, background: BackgroundTasks) -> dict[str, Any]:
    _state(run_id)
    try:
        background.add_task(pipeline.decide(run_id, number, body.approved, body.comment))
    except ValueError as exc:
        raise HTTPException(404, str(exc))
    except pipeline.Conflict as exc:
        raise HTTPException(409, str(exc))
    return {"run_id": run_id, "approval": number, "approved": body.approved}


@router.get("/runs/{run_id}/events")
async def stream_events(
    run_id: str,
    after: int = Query(0, ge=0),
    last_event_id: str | None = Header(None),
) -> EventSourceResponse:
    """Replay every past event, then stream new ones until the run is done or failed."""
    _state(run_id)
    cursor = after
    if last_event_id and last_event_id.isdigit():
        cursor = max(cursor, int(last_event_id))

    async def generate():
        nonlocal cursor
        while True:
            # Read the status first: events written after this read are picked up on the next loop.
            run = await asyncio.to_thread(store.get_run, run_id)
            for seq, event in await asyncio.to_thread(store.list_events, run_id, cursor):
                cursor = seq
                yield {"id": str(seq), "event": event.type.value, "data": event.model_dump_json()}
            if run is None or run.status in (RunStatus.done, RunStatus.failed):
                return
            await asyncio.sleep(POLL_SECONDS)

    return EventSourceResponse(generate())
