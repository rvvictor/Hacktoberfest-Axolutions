import json

import httpx
import pytest
import respx

from app.config import settings
from app.services import outreach
from app.services.outreach import (
    OPT_OUT_LINE,
    Outreach,
    OutreachError,
    OutreachStatus,
    apply_callback,
    approve,
    draft,
    get_prospect,
    load_prospects,
    send,
    sign_parts,
    start_flow,
    verify_callback,
    with_opt_out,
)

WEBHOOK = "https://n8n.example.test/webhook/hunter-outreach"
RESUME = "https://n8n.example.test/webhook-waiting/abc123"
SECRET = "test-secret-not-real"


@pytest.fixture(autouse=True)
def demo_settings(monkeypatch):
    """Tests never read a .env file or reach a real service."""
    monkeypatch.setattr(settings, "DEMO_MODE", True)
    monkeypatch.setattr(settings, "ANTHROPIC_API_KEY", None)
    monkeypatch.setattr(settings, "N8N_WEBHOOK_URL", None)
    monkeypatch.setattr(settings, "N8N_WEBHOOK_SECRET", None)


def _prospect(prospect_id="pros-barberia-001"):
    return get_prospect(prospect_id)


def test_fixture_prospects_are_fictitious_and_labeled():
    prospects = load_prospects()
    assert len(prospects) >= 2
    assert all(p.demo_data for p in prospects)
    assert any(p.opt_out for p in prospects)


def test_every_recorded_draft_carries_the_opt_out_line():
    for prospect in load_prospects():
        record = draft(prospect)
        assert record.status == OutreachStatus.DRAFT
        assert record.body.endswith(OPT_OUT_LINE)
        assert record.demo_data is True


def test_with_opt_out_appends_once():
    body = with_opt_out("Hola")
    assert body.endswith(OPT_OUT_LINE)
    assert with_opt_out(body) == body


def test_send_refuses_without_approval():
    prospect = _prospect()
    record = draft(prospect)
    with pytest.raises(OutreachError, match="not approved"):
        send(record, prospect)


@pytest.mark.parametrize("name", ["", "   ", None])
def test_approve_requires_a_named_human(name):
    record = draft(_prospect())
    with pytest.raises(OutreachError, match="approved_by is required"):
        approve(record, name)


def test_approve_then_in_process_send_marks_mock_sent():
    prospect = _prospect()
    record = start_flow(draft(prospect), prospect)
    assert record.transport == "in-process"
    approved = approve(record, "operador-demo")
    assert approved.status == OutreachStatus.APPROVED
    sent = send(approved, prospect)
    assert sent.status == OutreachStatus.SENT
    assert sent.approved_by == "operador-demo"
    assert sent.sent_at is not None
    assert sent.demo_data is True


def test_cannot_approve_twice():
    approved = approve(draft(_prospect()), "operador-demo")
    with pytest.raises(OutreachError, match="cannot approve"):
        approve(approved, "operador-demo")


def test_opted_out_prospect_is_skipped_even_when_approved():
    prospect = _prospect("pros-barberia-002")
    assert prospect.opt_out is True
    record = start_flow(draft(prospect), prospect)
    assert record.status == OutreachStatus.SKIPPED
    approved = approve(draft(prospect), "operador-demo")
    result = send(approved, prospect)
    assert result.status == OutreachStatus.SKIPPED
    assert result.sent_at is None


def test_send_rejects_a_record_for_another_prospect():
    approved = approve(draft(_prospect("pros-barberia-001")), "operador-demo")
    with pytest.raises(OutreachError, match="does not belong"):
        send(approved, _prospect("pros-barberia-003"))


def test_ai_draft_uses_the_api_and_still_gets_the_opt_out(monkeypatch):
    monkeypatch.setattr(settings, "DEMO_MODE", False)
    monkeypatch.setattr(settings, "ANTHROPIC_API_KEY", "test-key-not-real")
    with respx.mock(assert_all_called=True) as mock:
        route = mock.post(outreach.ANTHROPIC_URL).mock(
            return_value=httpx.Response(
                200, json={"content": [{"type": "text", "text": "Hola, demo de 15 minutos."}]}
            )
        )
        record = draft(_prospect())
    assert route.calls.last.request.headers["x-api-key"] == "test-key-not-real"
    assert record.body.startswith("Hola, demo de 15 minutos.")
    assert record.body.endswith(OPT_OUT_LINE)


def test_ai_draft_falls_back_to_the_recorded_draft_on_api_error(monkeypatch):
    monkeypatch.setattr(settings, "DEMO_MODE", False)
    monkeypatch.setattr(settings, "ANTHROPIC_API_KEY", "test-key-not-real")
    with respx.mock as mock:
        mock.post(outreach.ANTHROPIC_URL).mock(return_value=httpx.Response(500))
        record = draft(_prospect())
    assert "Barbería Ejemplo Norte" in record.body
    assert record.body.endswith(OPT_OUT_LINE)


def test_n8n_start_flow_signs_the_draft_and_stores_resume_url(monkeypatch):
    monkeypatch.setattr(settings, "N8N_WEBHOOK_URL", WEBHOOK)
    monkeypatch.setattr(settings, "N8N_WEBHOOK_SECRET", SECRET)
    prospect = _prospect()
    record = draft(prospect)
    with respx.mock as mock:
        route = mock.post(WEBHOOK).mock(
            return_value=httpx.Response(200, json={"resumeUrl": RESUME})
        )
        started = start_flow(record, prospect)
    request = route.calls.last.request
    body_bytes = request.content
    payload = json.loads(body_bytes)
    assert payload["stage"] == "draft"
    assert payload["body"] == record.body
    expected = sign_parts(
        SECRET,
        record.id,
        prospect.id,
        record.channel,
        outreach.body_digest(record.body),
    )
    assert request.headers[outreach.SIGNATURE_HEADER] == expected
    assert started.transport == "n8n"
    assert started.resume_url == RESUME


def test_n8n_send_resumes_the_wait_with_a_signed_approval(monkeypatch):
    monkeypatch.setattr(settings, "N8N_WEBHOOK_URL", WEBHOOK)
    monkeypatch.setattr(settings, "N8N_WEBHOOK_SECRET", SECRET)
    prospect = _prospect()
    record = draft(prospect)
    with respx.mock as mock:
        mock.post(WEBHOOK).mock(return_value=httpx.Response(200, json={"resumeUrl": RESUME}))
        resume = mock.post(RESUME).mock(return_value=httpx.Response(200, json={"status": "resumed"}))
        started = start_flow(record, prospect)
        approved = approve(started, "operador-demo")
        result = send(approved, prospect)
    request = resume.calls.last.request
    payload = json.loads(request.content)
    assert payload == {
        "stage": "approval",
        "outreach_id": record.id,
        "approved_by": "operador-demo",
        "opt_out": False,
        "demo_data": True,
    }
    expected = sign_parts(
        SECRET,
        record.id,
        prospect.id,
        record.channel,
        "operador-demo",
        outreach.body_digest(record.body),
    )
    assert request.headers[outreach.SIGNATURE_HEADER] == expected
    # The record only becomes SENT when n8n calls back.
    assert result.status == OutreachStatus.APPROVED


def test_n8n_transport_without_secret_is_refused(monkeypatch):
    monkeypatch.setattr(settings, "N8N_WEBHOOK_URL", WEBHOOK)
    with pytest.raises(OutreachError, match="N8N_WEBHOOK_SECRET is required"):
        start_flow(draft(_prospect()), _prospect())


def test_callback_must_be_signed_and_confirms_only_approved_sends(monkeypatch):
    monkeypatch.setattr(settings, "N8N_WEBHOOK_SECRET", SECRET)
    sent_at = "2026-10-27T12:00:00+00:00"
    good = sign_parts(SECRET, "out-1", "sent", sent_at)
    assert verify_callback(good, "out-1", "sent", sent_at) is True
    assert verify_callback(None, "out-1", "sent", sent_at) is False
    assert verify_callback("sha256=deadbeef", "out-1", "sent", sent_at) is False

    approved = approve(draft(_prospect()), "operador-demo")
    done = apply_callback(approved, "sent", sent_at)
    assert done.status == OutreachStatus.SENT
    assert done.demo_data is True
    with pytest.raises(OutreachError):
        apply_callback(draft(_prospect()), "sent", sent_at)


def test_outreach_model_round_trips():
    record = draft(_prospect())
    assert Outreach.model_validate_json(record.model_dump_json()) == record
