import json
from pathlib import Path

import httpx

from app.config import settings

API = "https://api.elevenlabs.io/v1"
FIXTURES = Path(__file__).resolve().parent.parent / "fixtures" / "voice"
AI_DISCLOSURE = "Hola, soy una voz generada por inteligencia artificial."
STT_MODEL = "scribe_v1"
TTS_MODEL = "eleven_multilingual_v2"


class VoiceUnavailable(RuntimeError):
    """A real ElevenLabs call was requested but the key, voice or agent is not configured."""


def _headers() -> dict[str, str]:
    if not settings.ELEVENLABS_API_KEY:
        raise VoiceUnavailable("ELEVENLABS_API_KEY is not set")
    return {"xi-api-key": settings.ELEVENLABS_API_KEY}


def recorded() -> bool:
    """Without a key, or in DEMO_MODE, the spoken audio is the recorded sample."""
    return bool(settings.DEMO_MODE) or not settings.ELEVENLABS_API_KEY


def with_disclosure(text: str) -> str:
    """Every spoken session opens by saying the voice is an AI."""
    return text if text.startswith(AI_DISCLOSURE) else f"{AI_DISCLOSURE} {text}"


async def transcribe(audio: bytes, filename: str, content_type: str) -> str:
    if settings.DEMO_MODE:
        return json.loads((FIXTURES / "stt.json").read_text())["text"]
    async with httpx.AsyncClient(timeout=60) as client:
        r = await client.post(
            f"{API}/speech-to-text",
            headers=_headers(),
            data={"model_id": STT_MODEL},
            files={"file": (filename, audio, content_type)},
        )
    r.raise_for_status()
    return r.json()["text"]


async def synthesize(text: str) -> bytes:
    if settings.DEMO_MODE:
        return (FIXTURES / "tts.mp3").read_bytes()
    headers = _headers()
    if not settings.ELEVENLABS_VOICE_ID:
        raise VoiceUnavailable("ELEVENLABS_VOICE_ID is not set")
    async with httpx.AsyncClient(timeout=60) as client:
        r = await client.post(
            f"{API}/text-to-speech/{settings.ELEVENLABS_VOICE_ID}",
            headers=headers,
            params={"output_format": "mp3_44100_128"},
            json={"text": text, "model_id": TTS_MODEL},
        )
    r.raise_for_status()
    return r.content


async def signed_url() -> str:
    """Signed Conversational AI URL, so the API key never reaches the browser."""
    if settings.DEMO_MODE:
        return "demo://elevenlabs-session"
    headers = _headers()
    if not settings.ELEVENLABS_AGENT_ID:
        raise VoiceUnavailable("ELEVENLABS_AGENT_ID is not set")
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.get(
            f"{API}/convai/conversation/get-signed-url",
            headers=headers,
            params={"agent_id": settings.ELEVENLABS_AGENT_ID},
        )
    r.raise_for_status()
    return r.json()["signed_url"]
