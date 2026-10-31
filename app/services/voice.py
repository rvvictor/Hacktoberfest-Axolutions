import json
import os
from datetime import UTC, datetime
from pathlib import Path

import httpx

from app.config import Settings, settings

API = "https://api.elevenlabs.io/v1"
FIXTURES = Path(__file__).resolve().parent.parent / "fixtures" / "voice"
AI_DISCLOSURE = "Hola, soy una voz generada por inteligencia artificial."
STT_MODEL = "scribe_v1"
TTS_MODEL = "eleven_multilingual_v2"


class VoiceUnavailable(RuntimeError):
    """A real ElevenLabs call was requested but the key, voice or agent is not configured."""


class VoiceBudgetExceeded(VoiceUnavailable):
    """Today's ElevenLabs character cap is spent: the deck stays usable without voice."""


def _cap() -> int:
    cap = settings.ELEVENLABS_DAILY_CHARS
    return Settings.model_fields["ELEVENLABS_DAILY_CHARS"].default if cap is None else cap


def _today() -> str:
    return datetime.now(UTC).date().isoformat()


def _counter() -> Path:
    return settings.DATA_DIR / "voice" / "chars.json"


def _spent() -> int:
    """Characters paid today. The file holds only the day and a number, never slide text."""
    try:
        data = json.loads(_counter().read_text())
    except (OSError, ValueError):
        return 0
    return data["chars"] if isinstance(data, dict) and data.get("day") == _today() and isinstance(data.get("chars"), int) else 0


def check_budget() -> None:
    if _spent() >= _cap():
        raise VoiceBudgetExceeded("ELEVENLABS_DAILY_CHARS is spent for today")


def spend(chars: int) -> None:
    """Reserve characters before paying for them; nothing awaits in between, so one process cannot overshoot."""
    total = _spent() + chars
    if total > _cap():
        raise VoiceBudgetExceeded("ELEVENLABS_DAILY_CHARS is spent for today")
    path = _counter()
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f"{path.name}.{os.getpid()}.tmp")
    tmp.write_text(json.dumps({"day": _today(), "chars": total}))
    os.replace(tmp, path)


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
    spend(len(text))
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
