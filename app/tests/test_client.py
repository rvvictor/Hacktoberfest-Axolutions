from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_journey_is_demo_data_and_plain() -> None:
    body = client.get("/api/client/journey").json()
    assert body["demo_data"] is True
    assert 3 <= len(body["questions"]) <= 5
    assert body["summary"]["points"]
    assert len(body["screens"]) >= 3


def test_whatsapp_preview_shows_opt_in_and_opt_out_and_is_not_sent() -> None:
    wa = client.get("/api/client/journey").json()["whatsapp"]
    assert wa["opt_in"] and wa["opt_out"]
    assert wa["sent"] is False


def test_link_is_a_demo_example_and_progress_has_one_current_step() -> None:
    body = client.get("/api/client/journey").json()
    assert ".invalid" in body["published_app"]["url"]
    states = [s["state"] for s in body["progress"]["steps"]]
    assert states.count("current") == 1
    assert 0 <= body["progress"]["percent"] <= 100


def test_audio_guide_has_transcript_and_no_paid_service() -> None:
    audio = client.get("/api/client/journey").json()["audio_guide"]
    assert audio["transcript"]
    assert audio["recorded_path"].startswith("app/fixtures/client/")
