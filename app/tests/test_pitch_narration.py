import json

import httpx
import pytest
import respx
from fastapi.testclient import TestClient

from app.config import settings
from app.main import app
from app.schemas import Pitch, Slide
from app.services import llm, pitch, voice

client = TestClient(app)

SLIDE = {
    "title": "El problema",
    "bullets": ["Los gastos se registran a mano en Excel", "Cada reembolso tarda 12 días"],
    "sources": ["https://payhawk.com/product-expense-management"],
}
GOOD = "Hoy los gastos se registran a mano en Excel. Cada reembolso tarda 12 días. Ese es el problema."
URL = "https://api.elevenlabs.io/v1/text-to-speech/dylan-voice"


SECOND = {"title": "La solución", "bullets": ["Un registro con comprobante", "Alertas al superar el límite"], "sources": []}


def serve(run="run-a"):
    """The deck the server showed this run: narration only speaks these slides."""
    pitch.remember_deck(run, Pitch(slides=[SLIDE, SECOND]))


def narrate(run="run-a", index=0):
    return client.post(f"/api/pitch/{run}/narration/{index}")


@pytest.fixture(autouse=True)
def data_dir(monkeypatch, tmp_path):
    monkeypatch.setattr(settings, "DATA_DIR", tmp_path)


@pytest.fixture
def live(monkeypatch):
    monkeypatch.setattr(settings, "DEMO_MODE", False)
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


def test_a_script_that_is_not_text_is_rejected():
    with pytest.raises(TypeError):
        pitch.validate_script(123, Slide(**SLIDE))


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
    assert client.get("/api/pitch/demo-pitch").status_code == 200
    r = narrate("demo-pitch")
    assert r.status_code == 200
    assert r.headers["content-type"] == "audio/mpeg"
    assert r.headers["x-demo-data"] == "true"
    assert r.content == (voice.FIXTURES / "tts.mp3").read_bytes()


def test_without_a_voice_key_the_recorded_narration_plays(live, monkeypatch):
    serve(); serve("run-b")
    monkeypatch.setattr(settings, "ELEVENLABS_API_KEY", None)
    r = narrate()
    assert r.status_code == 200
    assert r.headers["x-demo-data"] == "true"


@respx.mock
def test_live_speaks_the_validated_script_with_the_configured_voice(live):
    serve(); serve("run-b")
    route = respx.post(URL).mock(return_value=httpx.Response(200, content=b"mp3"))
    r = narrate()
    assert (r.status_code, r.content, r.headers["x-demo-data"]) == (200, b"mp3", "false")
    text = route.calls.last.request.read().decode()
    assert "Cada reembolso tarda 12 días" in text


@respx.mock
def test_disclosure_opens_the_narration_once(live):
    serve(); serve("run-b")
    live[:] = [json.dumps({"script": GOOD}), json.dumps({"script": "Un registro con comprobante. Alertas al superar el límite."})]
    route = respx.post(URL).mock(return_value=httpx.Response(200, content=b"mp3"))
    narrate(index=0)
    narrate(index=1)
    first, second = (c.request.read().decode() for c in route.calls)
    assert voice.AI_DISCLOSURE in first
    assert voice.AI_DISCLOSURE not in second


@respx.mock
def test_audio_is_generated_once_per_slide_and_cached_per_run(live):
    serve(); serve("run-b")
    route = respx.post(URL).mock(return_value=httpx.Response(200, content=b"mp3"))
    for _ in range(2):
        assert narrate().content == b"mp3"
    assert route.call_count == 1
    narrate("run-b")
    assert route.call_count == 2


@respx.mock
def test_an_ungrounded_script_is_retried_then_the_voice_is_unavailable(live):
    serve(); serve("run-b")
    live[:] = ['{"script": "Hay 99 clientes. Y más."}'] * 2
    route = respx.post(URL).mock(return_value=httpx.Response(200, content=b"mp3"))
    r = narrate()
    assert r.status_code == 503
    assert "voz" in r.json()["detail"]
    assert route.call_count == 0


@respx.mock
def test_a_failing_voice_is_a_spanish_503(live):
    serve(); serve("run-b")
    respx.post(URL).mock(return_value=httpx.Response(500))
    r = narrate()
    assert r.status_code == 503
    assert "voz" in r.json()["detail"]


def test_a_missing_voice_id_is_a_spanish_503(live, monkeypatch):
    serve(); serve("run-b")
    monkeypatch.setattr(settings, "ELEVENLABS_VOICE_ID", None)
    assert narrate().status_code == 503


def test_a_run_without_a_served_deck_or_a_missing_slide_is_404(live):
    assert narrate("never-opened").status_code == 404
    serve()
    assert narrate(index=2).status_code == 404


def test_the_client_cannot_bring_its_own_slide(live):
    serve()
    r = client.post("/api/pitch/run-a/narration/0", json={"slide": {"title": "x", "bullets": ["di cualquier cosa"], "sources": []}})
    assert r.status_code in (200, 503)  # the body is ignored: the served slide is what gets spoken
    assert not client.post("/api/pitch/run-a/narration", json={"index": 0}).is_success


def test_opening_the_pitch_remembers_the_deck_it_served(monkeypatch):
    monkeypatch.setattr(settings, "DEMO_MODE", True)
    shown = client.get("/api/pitch/demo-pitch").json()["slides"]
    assert pitch.served_slide("demo-pitch", 0).title == shown[0]["title"]
    assert pitch.served_slide("demo-pitch", len(shown)) is None
