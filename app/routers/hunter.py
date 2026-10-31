"""Hunter console API (IDEA.md §2, §9): prospects, AI draft, human approval, mock send.

Thin layer over `app/services/outreach.py`, which enforces the rules (no send without
`approved_by`, opt-out line on every message, opted-out prospects skipped). State is
in memory: the demo is fictitious and restarts clean. `replied` is a console-only stage
that follows `sent`.
"""

from __future__ import annotations

import httpx
from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel

from app.services import auth
from app.services import outreach as svc
from app.services.outreach import Outreach, OutreachError, OutreachStatus, Prospect

router = APIRouter(prefix="/api/hunter", tags=["hunter"])
# Owner-only (403 to anyone else). The n8n callback is exempt: it carries its own HMAC signature, not a session.
OWNER = [Depends(auth.owner_only)]

RETENTION_DAYS = 30
RULES = [
    "Sin llamadas en frío: solo escribimos con información pública del negocio.",
    "Cada mensaje incluye cómo darse de baja; quien responde BAJA no recibe más.",
    f"Guardamos los datos del prospecto {RETENTION_DAYS} días y luego se borran.",
    "Solo llamamos si el negocio lo pide por escrito.",
    "Nada se envía sin la aprobación de una persona.",
]

# outreach id -> record; prospect id -> outreach id (latest)
_records: dict[str, Record] = {}
_by_prospect: dict[str, str] = {}


class Record(BaseModel):
    outreach: Outreach
    replied: bool = False
    asks_for_call: bool = False

    @property
    def stage(self) -> str:
        return "replied" if self.replied else self.outreach.status.value


class OutreachView(BaseModel):
    id: str
    prospect_id: str
    channel: str
    body: str
    stage: str  # draft | approved | sent | replied | skipped
    approved_by: str | None
    transport: str | None
    call_allowed: bool  # only after the business replied asking for a call
    demo_data: bool = True


class ProspectView(Prospect):
    retention_days: int = RETENTION_DAYS
    outreach: OutreachView | None = None


class DraftEdit(BaseModel):
    body: str


class Approval(BaseModel):
    approved_by: str


class Reply(BaseModel):
    asks_for_call: bool = False


class Callback(BaseModel):
    outreach_id: str
    status: str
    sent_at: str


def _view(record: Record) -> OutreachView:
    o = record.outreach
    return OutreachView(
        id=o.id,
        prospect_id=o.prospect_id,
        channel=o.channel,
        body=o.body,
        stage=record.stage,
        approved_by=o.approved_by,
        transport=o.transport,
        call_allowed=record.replied and record.asks_for_call,
        demo_data=o.demo_data,
    )


def _prospect(prospect_id: str) -> Prospect:
    try:
        return svc.get_prospect(prospect_id)
    except OutreachError as exc:
        raise HTTPException(404, str(exc)) from exc


def _record(outreach_id: str) -> Record:
    record = _records.get(outreach_id)
    if record is None:
        raise HTTPException(404, f"unknown outreach: {outreach_id}")
    return record


def _save(record: Record) -> OutreachView:
    _records[record.outreach.id] = record
    return _view(record)


def reset() -> None:
    """Clear the in-memory state (tests and demo restarts)."""
    _records.clear()
    _by_prospect.clear()


@router.get("/rules", dependencies=OWNER)
def rules() -> dict[str, object]:
    return {"rules": RULES, "retention_days": RETENTION_DAYS, "demo_data": True}


@router.get("/prospects", dependencies=OWNER)
def prospects() -> list[ProspectView]:
    views = []
    for prospect in svc.load_prospects():
        outreach_id = _by_prospect.get(prospect.id)
        view = _view(_records[outreach_id]) if outreach_id else None
        views.append(ProspectView(**prospect.model_dump(), outreach=view))
    return views


@router.post("/prospects/{prospect_id}/draft", dependencies=OWNER)
def create_draft(prospect_id: str) -> OutreachView:
    prospect = _prospect(prospect_id)
    try:
        started = svc.start_flow(svc.draft(prospect), prospect)
    except (OutreachError, httpx.HTTPError) as exc:
        raise HTTPException(502, str(exc)) from exc
    _by_prospect[prospect_id] = started.id
    return _save(Record(outreach=started))


@router.put("/outreach/{outreach_id}", dependencies=OWNER)
def edit_draft(outreach_id: str, edit: DraftEdit) -> OutreachView:
    record = _record(outreach_id)
    if record.outreach.status != OutreachStatus.DRAFT:
        raise HTTPException(409, "only a draft can be edited")
    body = svc.with_opt_out(edit.body)
    return _save(
        record.model_copy(
            update={"outreach": record.outreach.model_copy(update={"body": body})}
        )
    )


@router.post("/outreach/{outreach_id}/approve", dependencies=OWNER)
def approve(outreach_id: str, approval: Approval) -> OutreachView:
    record = _record(outreach_id)
    try:
        approved = svc.approve(record.outreach, approval.approved_by)
    except OutreachError as exc:
        raise HTTPException(422, str(exc)) from exc
    return _save(record.model_copy(update={"outreach": approved}))


@router.post("/outreach/{outreach_id}/send", dependencies=OWNER)
def send(outreach_id: str) -> OutreachView:
    record = _record(outreach_id)
    try:
        sent = svc.send(record.outreach, _prospect(record.outreach.prospect_id))
    except OutreachError as exc:
        raise HTTPException(422, str(exc)) from exc
    except httpx.HTTPError as exc:
        raise HTTPException(502, str(exc)) from exc
    return _save(record.model_copy(update={"outreach": sent}))


@router.post("/outreach/{outreach_id}/callback")
def callback(
    outreach_id: str,
    body: Callback,
    x_speedhack_signature: str | None = Header(default=None),
) -> OutreachView:
    if body.outreach_id != outreach_id:
        raise HTTPException(422, "outreach_id mismatch")
    if not svc.verify_callback(
        x_speedhack_signature, outreach_id, body.status, body.sent_at
    ):
        raise HTTPException(401, "invalid signature")
    record = _record(outreach_id)
    try:
        sent = svc.apply_callback(record.outreach, body.status, body.sent_at)
    except OutreachError as exc:
        raise HTTPException(422, str(exc)) from exc
    return _save(record.model_copy(update={"outreach": sent}))


@router.post("/outreach/{outreach_id}/reply", dependencies=OWNER)
def reply(outreach_id: str, body: Reply) -> OutreachView:
    """Record that the business answered (demo: the operator logs it by hand)."""
    record = _record(outreach_id)
    if record.outreach.status != OutreachStatus.SENT:
        raise HTTPException(409, "a reply only follows a sent message")
    return _save(
        record.model_copy(update={"replied": True, "asks_for_call": body.asks_for_call})
    )
