import httpx
import pytest
import respx
from fastapi.testclient import TestClient

from app.config import settings
from app.main import app
from app.services import voice

client = TestClient(app)


@pytest.fixture
def demo(monkeypatch):
    monkeypatch.setattr(settings, "DEMO_MODE", True)


@pytest.fixture
def live(monkeypatch):
    monkeypatch.setattr(settings, "DEMO_MODE", False)
    monkeypatch.setattr(settings, "ELEVENLABS_API_KEY", "test-key")
    monkeypatch.setattr(settings, "ELEVENLABS_VOICE_ID", "voice1")
    monkeypatch.setattr(settings, "ELEVENLABS_AGENT_ID", "agent1")


def test_stt_demo_returns_recorded_transcript(demo):
    r = client.post("/api/voice/stt", files={"audio": ("a.webm", b"x", "audio/webm")})
    assert r.status_code == 200
    assert "control de gastos" in r.json()["text"]


def test_tts_demo_returns_recorded_mpeg(demo):
    r = client.post("/api/voice/tts", json={"text": "hola"})
    assert r.status_code == 200
    assert r.headers["content-type"] == "audio/mpeg"
    assert r.content


def test_session_demo_has_disclosure(demo):
    r = client.get("/api/voice/session")
    assert r.status_code == 200
    assert "inteligencia artificial" in r.json()["disclosure"]


@respx.mock
def test_tts_live_prepends_ai_disclosure(live):
    route = respx.post("https://api.elevenlabs.io/v1/text-to-speech/voice1").mock(
        return_value=httpx.Response(200, content=b"mp3")
    )
    r = client.post("/api/voice/tts", json={"text": "hola"})
    assert r.content == b"mp3"
    sent = route.calls[0].request
    assert sent.headers["xi-api-key"] == "test-key"
    assert voice.AI_DISCLOSURE in sent.content.decode()


@respx.mock
def test_stt_live_posts_audio(live):
    respx.post("https://api.elevenlabs.io/v1/speech-to-text").mock(
        return_value=httpx.Response(200, json={"text": "hola mundo"})
    )
    r = client.post("/api/voice/stt", files={"audio": ("a.webm", b"x", "audio/webm")})
    assert r.json() == {"text": "hola mundo"}


@respx.mock
def test_session_live_returns_signed_url_not_key(live):
    respx.get("https://api.elevenlabs.io/v1/convai/conversation/get-signed-url").mock(
        return_value=httpx.Response(200, json={"signed_url": "wss://signed"})
    )
    r = client.get("/api/voice/session")
    assert r.json()["signed_url"] == "wss://signed"
    assert "test-key" not in r.text


def test_live_without_key_is_503(monkeypatch):
    monkeypatch.setattr(settings, "DEMO_MODE", False)
    monkeypatch.setattr(settings, "ELEVENLABS_API_KEY", None)
    assert client.post("/api/voice/tts", json={"text": "x"}).status_code == 503
