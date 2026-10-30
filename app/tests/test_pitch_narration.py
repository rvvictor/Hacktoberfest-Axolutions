import json

import httpx
import pytest
import respx
from fastapi.testclient import TestClient

from app.config import settings
from app.main import app
from app.schemas import Slide
from app.services import llm, pitch, voice

client = TestClient(app)

SLIDE = {
    "title": "El problema",
    "bullets": ["Los gastos se registran a mano en Excel", "Cada reembolso tarda 12 días"],
    "sources": ["https://payhawk.com/product-expense-management"],
}
GOOD = "Hoy los gastos se registran a mano en Excel. Cada reembolso tarda 12 días. Ese es el problema."
URL = "https://api.elevenlabs.io/v1/text-to-speech/dylan-voice"


def body(index=0, slide=SLIDE):
    return {"index": index, "slide": slide}


@pytest.fixture
def live(monkeypatch, tmp_path):
    monkeypatch.setattr(settings, "DEMO_MODE", False)
    monkeypatch.setattr(settings, "DATA_DIR", tmp_path)
    monkeypatch.setattr(settings, "ANTHROPIC_API_KEY", "k")
    monkeypatch.setattr(settings, "ELEVENLABS_API_KEY", "xi")
    monkeypatch.setattr(settings, "ELEVENLABS_VOICE_ID", "dylan-voice")
    scripts = []
    monkeypatch.setattr(
        llm, "_complete", lambda system, user, **kw: scripts.pop(0) if scripts else json.dumps({"script": GOOD})
    )
    return scripts


# --- script validation -------------------------------------------------------


def test_script_with_a_figure_not_on_the_slide_is_rejected():
    with pytest.raises(ValueError, match="figures"):
        pitch.validate_script("Los gastos van en Excel. Cada reembolso tarda 30 días.", Slide(**SLIDE))


def test_script_with_a_name_not_on_the_slide_is_rejected():
    with pytest.raises(ValueError, match="Salesforce"):
        pitch.validate_script("Los gastos van en Excel. Competimos con Salesforce en esto.", Slide(**SLIDE))


def test_script_must_have_two_to_four_sentences():
    slide = Slide(**SLIDE)
    with pytest.raises(ValueError, match="sentences"):
        pitch.validate_script("Los gastos van en Excel.", slide)
    with pytest.raises(ValueError, match="sentences"):
        pitch.validate_script("Uno. Dos. Tres. Cuatro. Cinco.", slide)


def test_grounded_script_passes():
    assert pitch.validate_script(GOOD, Slide(**SLIDE)) == GOOD


# --- endpoint ----------------------------------------------------------------


def test_demo_plays_the_recorded_narration_labeled_demo(monkeypatch):
    monkeypatch.setattr(settings, "DEMO_MODE", True)
    r = client.post("/api/pitch/demo-pitch/narration", json=body())
    assert r.status_code == 200
    assert r.headers["content-type"] == "audio/mpeg"
    assert r.headers["x-demo-data"] == "true"
    assert r.content == (voice.FIXTURES / "tts.mp3").read_bytes()


def test_without_a_voice_key_the_recorded_narration_plays(live, monkeypatch):
    monkeypatch.setattr(settings, "ELEVENLABS_API_KEY", None)
    r = client.post("/api/pitch/run-a/narration", json=body())
    assert r.status_code == 200
    assert r.headers["x-demo-data"] == "true"


@respx.mock
def test_live_speaks_the_validated_script_with_the_configured_voice(live):
    route = respx.post(URL).mock(return_value=httpx.Response(200, content=b"mp3"))
    r = client.post("/api/pitch/run-a/narration", json=body())
    assert (r.status_code, r.content, r.headers["x-demo-data"]) == (200, b"mp3", "false")
    text = route.calls.last.request.read().decode()
    assert "Cada reembolso tarda 12 días" in text


@respx.mock
def test_disclosure_opens_the_narration_once(live):
    route = respx.post(URL).mock(return_value=httpx.Response(200, content=b"mp3"))
    client.post("/api/pitch/run-a/narration", json=body(0))
    client.post("/api/pitch/run-a/narration", json=body(1))
    first, second = (c.request.read().decode() for c in route.calls)
    assert voice.AI_DISCLOSURE in first
    assert voice.AI_DISCLOSURE not in second


@respx.mock
def test_audio_is_generated_once_per_slide_and_cached_per_run(live):
    route = respx.post(URL).mock(return_value=httpx.Response(200, content=b"mp3"))
    for _ in range(2):
        assert client.post("/api/pitch/run-a/narration", json=body()).content == b"mp3"
    assert route.call_count == 1
    client.post("/api/pitch/run-b/narration", json=body())
    assert route.call_count == 2


@respx.mock
def test_an_ungrounded_script_is_retried_then_the_voice_is_unavailable(live):
    live[:] = ['{"script": "Hay 99 clientes. Y más."}'] * 2
    route = respx.post(URL).mock(return_value=httpx.Response(200, content=b"mp3"))
    r = client.post("/api/pitch/run-a/narration", json=body())
    assert r.status_code == 503
    assert "voz" in r.json()["detail"]
    assert route.call_count == 0


@respx.mock
def test_a_failing_voice_is_a_spanish_503(live):
    respx.post(URL).mock(return_value=httpx.Response(500))
    r = client.post("/api/pitch/run-a/narration", json=body())
    assert r.status_code == 503
    assert "voz" in r.json()["detail"]


def test_a_missing_voice_id_is_a_spanish_503(live, monkeypatch):
    monkeypatch.setattr(settings, "ELEVENLABS_VOICE_ID", None)
    assert client.post("/api/pitch/run-a/narration", json=body()).status_code == 503
