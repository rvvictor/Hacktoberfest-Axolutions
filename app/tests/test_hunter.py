import pytest
from fastapi.testclient import TestClient

from app.config import settings
from app.main import app
from app.routers import hunter
from app.services.outreach import OPT_OUT_LINE, sign_parts

client = TestClient(app)
P1, P_OPT_OUT = "pros-barberia-001", "pros-barberia-002"


@pytest.fixture(autouse=True)
def clean(monkeypatch):
    hunter.reset()
    monkeypatch.setattr(settings, "DEMO_MODE", True)
    monkeypatch.setattr(settings, "ANTHROPIC_API_KEY", None)
    monkeypatch.setattr(settings, "N8N_WEBHOOK_URL", None)
    monkeypatch.setattr(settings, "N8N_WEBHOOK_SECRET", None)


def _draft(prospect_id=P1):
    return client.post(f"/api/hunter/prospects/{prospect_id}/draft").json()


def test_prospects_are_fictional_public_info():
    data = client.get("/api/hunter/prospects").json()
    assert len(data) >= 3
    assert all(p["demo_data"] is True and p["outreach"] is None for p in data)
    assert all(p["public_source_url"].startswith("https://example.com/") for p in data)
    assert {p["retention_days"] for p in data} == {30}


def test_rules_listed():
    data = client.get("/api/hunter/rules").json()
    text = " ".join(data["rules"]).lower()
    for word in ("llamadas en frío", "baja", "30 días", "lo pide"):
        assert word in text


def test_full_flow_draft_approved_sent_replied():
    draft = _draft()
    assert draft["stage"] == "draft" and OPT_OUT_LINE in draft["body"]
    edited = client.put(
        f"/api/hunter/outreach/{draft['id']}", json={"body": "Hola, demo de 15 min."}
    ).json()
    assert edited["body"].startswith("Hola, demo") and OPT_OUT_LINE in edited["body"]
    approved = client.post(
        f"/api/hunter/outreach/{draft['id']}/approve", json={"approved_by": "Ana"}
    ).json()
    assert approved["stage"] == "approved" and approved["approved_by"] == "Ana"
    sent = client.post(f"/api/hunter/outreach/{draft['id']}/send").json()
    assert (
        sent["stage"] == "sent"
        and sent["transport"] == "in-process"
        and sent["demo_data"] is True
    )
    replied = client.post(
        f"/api/hunter/outreach/{draft['id']}/reply", json={"asks_for_call": True}
    ).json()
    assert replied["stage"] == "replied" and replied["call_allowed"] is True
    listed = client.get("/api/hunter/prospects").json()
    assert next(p for p in listed if p["id"] == P1)["outreach"]["stage"] == "replied"


def test_no_send_without_approval():
    draft = _draft()
    assert client.post(f"/api/hunter/outreach/{draft['id']}/send").status_code == 422
    blank = client.post(
        f"/api/hunter/outreach/{draft['id']}/approve", json={"approved_by": " "}
    )
    assert blank.status_code == 422


def test_cannot_edit_after_approval():
    draft = _draft()
    client.post(
        f"/api/hunter/outreach/{draft['id']}/approve", json={"approved_by": "Ana"}
    )
    assert (
        client.put(
            f"/api/hunter/outreach/{draft['id']}", json={"body": "x"}
        ).status_code
        == 409
    )


def test_opted_out_prospect_is_skipped():
    draft = _draft(P_OPT_OUT)
    assert draft["stage"] == "skipped"
    assert (
        client.post(
            f"/api/hunter/outreach/{draft['id']}/approve", json={"approved_by": "Ana"}
        ).status_code
        == 422
    )


def test_call_not_allowed_unless_business_asks():
    draft = _draft()
    client.post(
        f"/api/hunter/outreach/{draft['id']}/approve", json={"approved_by": "Ana"}
    )
    client.post(f"/api/hunter/outreach/{draft['id']}/send")
    assert (
        client.post(f"/api/hunter/outreach/{draft['id']}/reply", json={}).json()[
            "call_allowed"
        ]
        is False
    )


def test_reply_requires_sent():
    draft = _draft()
    assert (
        client.post(f"/api/hunter/outreach/{draft['id']}/reply", json={}).status_code
        == 409
    )


def test_unknown_ids_404():
    assert client.post("/api/hunter/prospects/nope/draft").status_code == 404
    assert client.post("/api/hunter/outreach/nope/send").status_code == 404


def test_callback_needs_valid_signature(monkeypatch):
    monkeypatch.setattr(settings, "N8N_WEBHOOK_SECRET", "test-secret-not-real")
    draft = _draft()
    client.post(
        f"/api/hunter/outreach/{draft['id']}/approve", json={"approved_by": "Ana"}
    )
    body = {
        "outreach_id": draft["id"],
        "status": "sent",
        "sent_at": "2026-10-27T12:00:00+00:00",
    }
    url = f"/api/hunter/outreach/{draft['id']}/callback"
    assert client.post(url, json=body).status_code == 401
    sig = sign_parts("test-secret-not-real", draft["id"], "sent", body["sent_at"])
    ok = client.post(url, json=body, headers={"X-SpeedHack-Signature": sig})
    assert ok.status_code == 200 and ok.json()["stage"] == "sent"
