import asyncio
import json

import httpx
import pytest
import respx
from fastapi.testclient import TestClient

from app.config import settings
from app.main import app
from app.schemas import Pitch
from app.services import llm, pitch, voice

client = TestClient(app)

SLIDE = {
    "title": "El problema",
    "bullets": ["Los gastos se registran a mano en Excel", "Cada reembolso tarda 12 días"],
    "sources": [],
}
SECOND = {"title": "La solución", "bullets": ["Un registro con comprobante", "Alertas al superar el límite"], "sources": []}
GOOD = "Hoy los gastos se registran a mano en Excel. Cada reembolso tarda 12 días. Ese es el problema."
GOOD_SECOND = "Un registro con comprobante. Alertas al superar el límite. Esa es la solución."
URL = "https://api.elevenlabs.io/v1/text-to-speech/dylan-voice"


@pytest.fixture(autouse=True)
def data_dir(monkeypatch, tmp_path):
    monkeypatch.setattr(settings, "DATA_DIR", tmp_path)
    pitch.remember_deck("run-a", Pitch(slides=[SLIDE, SECOND]))


@pytest.fixture
def live(monkeypatch):
    monkeypatch.setattr(settings, "DEMO_MODE", False)
    monkeypatch.setattr(settings, "ANTHROPIC_API_KEY", "k")
    monkeypatch.setattr(settings, "ELEVENLABS_API_KEY", "xi")
    monkeypatch.setattr(settings, "ELEVENLABS_VOICE_ID", "dylan-voice")
    monkeypatch.setattr(llm, "_complete", lambda system, user, **kw: json.dumps({"script": script_for(user)}))


def script_for(user):
    return GOOD_SECOND if "comprobante" in user else GOOD


def test_concurrent_requests_for_one_slide_pay_for_one_script_and_one_voice(live, monkeypatch):
    calls = {"script": 0, "tts": 0}

    def script(slide):
        calls["script"] += 1
        return GOOD

    async def tts(text):
        calls["tts"] += 1
        await asyncio.sleep(0.01)
        return b"mp3"

    monkeypatch.setattr(pitch, "narration_script", script)
    monkeypatch.setattr(voice, "synthesize", tts)

    async def burst():
        return await asyncio.gather(*(pitch.narrate("run-a", 1) for _ in range(6)))

    results = asyncio.run(burst())
    assert {audio for audio, _ in results} == {b"mp3"}
    assert calls == {"script": 1, "tts": 1}


@respx.mock
def test_the_daily_cap_answers_503_in_spanish_and_stops_paying(live, monkeypatch):
    monkeypatch.setattr(settings, "ELEVENLABS_DAILY_CHARS", len(GOOD) + len(voice.AI_DISCLOSURE) + 1)  # room for slide 0 only
    route = respx.post(URL).mock(return_value=httpx.Response(200, content=b"mp3"))
    assert client.post("/api/pitch/run-a/narration/0").status_code == 200
    capped = client.post("/api/pitch/run-a/narration/1")
    assert capped.status_code == 503
    assert "voz" in capped.json()["detail"]
    assert route.call_count == 1


@respx.mock
def test_a_capped_day_does_not_pay_for_the_script_either(live, monkeypatch):
    monkeypatch.setattr(settings, "ELEVENLABS_DAILY_CHARS", 0)
    paid = []
    monkeypatch.setattr(llm, "_complete", lambda system, user, **kw: paid.append(1) or json.dumps({"script": GOOD_SECOND}))
    route = respx.post(URL).mock(return_value=httpx.Response(200, content=b"mp3"))
    assert client.post("/api/pitch/run-a/narration/1").status_code == 503
    assert paid == [] and route.call_count == 0


@respx.mock
def test_cached_audio_is_served_after_the_cap_is_reached(live, monkeypatch):
    respx.post(URL).mock(return_value=httpx.Response(200, content=b"mp3"))
    assert client.post("/api/pitch/run-a/narration/1").status_code == 200
    monkeypatch.setattr(settings, "ELEVENLABS_DAILY_CHARS", 0)
    again = client.post("/api/pitch/run-a/narration/1")
    assert again.status_code == 200 and again.content == b"mp3"


def test_the_count_lives_on_disk_and_never_stores_slide_text(live, monkeypatch):
    async def go():
        voice.spend(120)
        voice.spend(30)

    asyncio.run(go())
    files = list((settings.DATA_DIR / "voice").glob("*"))
    assert len(files) == 1
    assert json.loads(files[0].read_text())["chars"] == 150
    assert "Excel" not in files[0].read_text() and "problema" not in files[0].read_text()


def test_the_count_starts_over_the_next_day(live, monkeypatch):
    monkeypatch.setattr(settings, "ELEVENLABS_DAILY_CHARS", 100)
    monkeypatch.setattr(voice, "_today", lambda: "2026-10-30")
    voice.spend(100)
    with pytest.raises(voice.VoiceBudgetExceeded):
        voice.spend(1)
    monkeypatch.setattr(voice, "_today", lambda: "2026-10-31")
    voice.spend(100)


def test_recorded_demo_audio_is_free(monkeypatch):
    monkeypatch.setattr(settings, "ELEVENLABS_DAILY_CHARS", 0)
    assert client.post("/api/pitch/run-a/narration/0").status_code == 200
