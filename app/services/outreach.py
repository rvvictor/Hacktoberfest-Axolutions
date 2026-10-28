"""Outreach flow for the Hunter agent (IDEA.md §4 step 5, §7, §9).

draft (AI) -> human approval -> send -> callback. Send goes to the n8n webhook when
N8N_WEBHOOK_URL is set, otherwise the same steps run in-process, so the demo never
depends on n8n being up.

Rules, enforced here and not only in the UI:
- nothing is sent without `approved_by`;
- every message carries the opt-out line;
- a prospect with `opt_out` is skipped;
- the send is a mock (no real email or WhatsApp) and every record says demo_data.
Prospects are fictitious (app/fixtures/outreach/prospects.json).
"""

from __future__ import annotations

import hashlib
import hmac
import json
import uuid
from datetime import UTC, datetime
from enum import Enum
from pathlib import Path

import httpx
from pydantic import BaseModel

from app.config import settings

FIXTURES = Path(__file__).resolve().parent.parent / "fixtures" / "outreach"
OPT_OUT_LINE = "Si no quieres recibir más mensajes, responde BAJA y no te escribiremos de nuevo."
ANTHROPIC_URL = "https://api.anthropic.com/v1/messages"
SIGNATURE_HEADER = "X-SpeedHack-Signature"
TIMEOUT = 10.0


class OutreachError(ValueError):
    """Raised when a rule blocks the flow (no approval, missing secret, bad state)."""


class OutreachStatus(str, Enum):
    DRAFT = "draft"
    APPROVED = "approved"
    SENT = "sent"  # mock send only: demo_data is always true
    SKIPPED = "skipped"  # prospect opted out; nothing was sent


class Prospect(BaseModel):
    id: str
    business: str
    city: str
    public_pain: str
    public_source_url: str
    channel: str
    contact: str
    opt_out: bool = False
    demo_data: bool = True


class Outreach(BaseModel):
    id: str
    prospect_id: str
    channel: str
    body: str
    status: OutreachStatus = OutreachStatus.DRAFT
    approved_by: str | None = None
    transport: str | None = None  # "n8n" | "in-process"
    resume_url: str | None = None  # n8n Wait node resume URL, set by start_flow
    sent_at: datetime | None = None
    demo_data: bool = True


def load_prospects() -> list[Prospect]:
    data = json.loads((FIXTURES / "prospects.json").read_text(encoding="utf-8"))
    return [Prospect(**item) for item in data["prospects"]]


def get_prospect(prospect_id: str) -> Prospect:
    for prospect in load_prospects():
        if prospect.id == prospect_id:
            return prospect
    raise OutreachError(f"unknown prospect: {prospect_id}")


def with_opt_out(body: str) -> str:
    """Append the opt-out line if the draft lacks it. Every message carries it."""
    text = body.strip()
    if OPT_OUT_LINE in text:
        return text
    return f"{text}\n\n{OPT_OUT_LINE}"


def _fixture_draft(prospect: Prospect) -> str:
    data = json.loads((FIXTURES / "drafts.json").read_text(encoding="utf-8"))
    return data["drafts"].get(
        prospect.id,
        f"Hola, equipo de {prospect.business}: armamos una demo para barberías como la suya.",
    )


def ai_draft(prospect: Prospect, client: httpx.Client | None = None) -> str:
    """AI draft. Recorded fixture in DEMO_MODE, without a key, or when the API fails."""
    if settings.DEMO_MODE or not settings.ANTHROPIC_API_KEY:
        return _fixture_draft(prospect)
    prompt = (
        "Escribe un mensaje corto y cordial en español para un negocio ficticio. "
        "Usa solo esta información pública y no inventes datos personales ni cifras. "
        f"Negocio: {prospect.business}. Dato público: {prospect.public_pain}. "
        "Ofrece una demo de 15 minutos. No incluyas la línea de baja; la agrega el sistema."
    )
    headers = {
        "x-api-key": settings.ANTHROPIC_API_KEY,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json",
    }
    payload = {
        "model": settings.LLM_MODEL,
        "max_tokens": 300,
        "messages": [{"role": "user", "content": prompt}],
    }
    try:
        http = client or httpx.Client(timeout=TIMEOUT)
        response = http.post(ANTHROPIC_URL, headers=headers, json=payload)
        response.raise_for_status()
        return response.json()["content"][0]["text"]
    except (httpx.HTTPError, KeyError, IndexError, ValueError):
        return _fixture_draft(prospect)


def draft(prospect: Prospect, client: httpx.Client | None = None) -> Outreach:
    body = with_opt_out(ai_draft(prospect, client))
    return Outreach(
        id=f"out-{uuid.uuid4().hex[:8]}",
        prospect_id=prospect.id,
        channel=prospect.channel,
        body=body,
    )


def approve(outreach: Outreach, approved_by: str) -> Outreach:
    name = (approved_by or "").strip()
    if not name:
        raise OutreachError("approved_by is required: nothing is sent without a human approval")
    if outreach.status != OutreachStatus.DRAFT:
        raise OutreachError(f"cannot approve from status {outreach.status.value}")
    return outreach.model_copy(update={"status": OutreachStatus.APPROVED, "approved_by": name})


def body_digest(body: str) -> str:
    return hashlib.sha256(body.encode("utf-8")).hexdigest()


def sign_parts(secret: str, *parts: str) -> str:
    """HMAC-SHA256 over the parts joined by newline. n8n computes the same string."""
    message = "\n".join(parts).encode("utf-8")
    return "sha256=" + hmac.new(secret.encode("utf-8"), message, hashlib.sha256).hexdigest()


def verify_parts(secret: str, signature: str | None, *parts: str) -> bool:
    if not secret or not signature:
        return False
    return hmac.compare_digest(sign_parts(secret, *parts), signature)


def _now() -> datetime:
    return datetime.now(UTC)


def start_flow(outreach: Outreach, prospect: Prospect, client: httpx.Client | None = None) -> Outreach:
    """Hand the draft to n8n, which waits for approval, or mark in-process transport."""
    if prospect.opt_out:
        return outreach.model_copy(update={"status": OutreachStatus.SKIPPED})
    if not settings.N8N_WEBHOOK_URL:
        return outreach.model_copy(update={"transport": "in-process"})
    if not settings.N8N_WEBHOOK_SECRET:
        raise OutreachError("N8N_WEBHOOK_SECRET is required when N8N_WEBHOOK_URL is set")
    parts = (outreach.id, prospect.id, outreach.channel, body_digest(outreach.body))
    payload = {
        "stage": "draft",
        "outreach_id": outreach.id,
        "prospect_id": prospect.id,
        "channel": outreach.channel,
        "body": outreach.body,
        "demo_data": True,
    }
    headers = {SIGNATURE_HEADER: sign_parts(settings.N8N_WEBHOOK_SECRET, *parts)}
    http = client or httpx.Client(timeout=TIMEOUT)
    response = http.post(settings.N8N_WEBHOOK_URL, headers=headers, json=payload)
    response.raise_for_status()
    return outreach.model_copy(
        update={"transport": "n8n", "resume_url": response.json().get("resumeUrl")}
    )


def send(outreach: Outreach, prospect: Prospect, client: httpx.Client | None = None) -> Outreach:
    """Send the approved draft (mock). Returns the updated record."""
    if outreach.prospect_id != prospect.id:
        raise OutreachError("outreach does not belong to this prospect")
    if not outreach.approved_by or outreach.status != OutreachStatus.APPROVED:
        raise OutreachError("not approved: nothing is sent without approved_by")
    if prospect.opt_out:
        return outreach.model_copy(update={"status": OutreachStatus.SKIPPED})

    if outreach.transport == "n8n":
        if not settings.N8N_WEBHOOK_SECRET:
            raise OutreachError("N8N_WEBHOOK_SECRET is required to resume the n8n flow")
        if not outreach.resume_url:
            raise OutreachError("n8n flow has no resume_url: call start_flow first")
        parts = (outreach.id, prospect.id, outreach.channel, outreach.approved_by, body_digest(outreach.body))
        payload = {
            "stage": "approval",
            "outreach_id": outreach.id,
            "approved_by": outreach.approved_by,
            "opt_out": False,
            "demo_data": True,
        }
        headers = {SIGNATURE_HEADER: sign_parts(settings.N8N_WEBHOOK_SECRET, *parts)}
        http = client or httpx.Client(timeout=TIMEOUT)
        response = http.post(outreach.resume_url, headers=headers, json=payload)
        response.raise_for_status()
        # The n8n callback (apply_callback) moves the record to sent once the mock send ran.
        return outreach

    return outreach.model_copy(
        update={"status": OutreachStatus.SENT, "transport": "in-process", "sent_at": _now()}
    )


def verify_callback(signature: str | None, outreach_id: str, status: str, sent_at: str) -> bool:
    """Check the signed n8n callback. Unsigned or wrongly signed callbacks are refused."""
    return verify_parts(settings.N8N_WEBHOOK_SECRET or "", signature, outreach_id, status, sent_at)


def apply_callback(outreach: Outreach, status: str, sent_at: str) -> Outreach:
    if status != OutreachStatus.SENT.value or not outreach.approved_by:
        raise OutreachError("callback can only confirm an approved send")
    return outreach.model_copy(
        update={
            "status": OutreachStatus.SENT,
            "sent_at": datetime.fromisoformat(sent_at),
            "demo_data": True,
        }
    )
