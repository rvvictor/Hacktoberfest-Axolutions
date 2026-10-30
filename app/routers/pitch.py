import httpx
from anthropic import APIError
from fastapi import APIRouter, HTTPException, Response
from pydantic import BaseModel, Field, field_validator

from app.schemas import Pitch
from app.services import llm, pitch, voice

router = APIRouter(prefix="/api/pitch", tags=["pitch"])


class Question(BaseModel):
    question: str = Field(min_length=1, max_length=2000)

    @field_validator("question")
    @classmethod
    def nonempty(cls, value):
        if not value.strip():
            raise ValueError("Escribe una pregunta")
        return value.strip()


@router.post("/{run_id}/narration/{index}")
async def narrate(run_id: str, index: int) -> Response:
    try:
        spoken = await pitch.narrate(run_id, index)
    except (voice.VoiceUnavailable, llm.LLMError, APIError, httpx.HTTPError, OSError) as exc:
        raise HTTPException(503, "La voz no está disponible. Lee el texto de la diapositiva.") from exc
    if spoken is None:
        raise HTTPException(404, "Esa diapositiva no existe. Abre el pitch de nuevo.")
    audio, demo = spoken
    return Response(audio, media_type="audio/mpeg", headers={"X-Demo-Data": str(demo).lower()})


@router.get("/{run_id}", response_model=Pitch)
def get_deck(run_id: str):
    try:
        result = pitch.deck(run_id)
        pitch.remember_deck(run_id, result)
        return result
    except (pitch.PitchUnavailable, llm.LLMError, APIError, OSError) as exc:
        raise HTTPException(
            503, "No se pudo preparar el pitch. Intenta de nuevo."
        ) from exc


@router.post("/{run_id}/ask", response_model=pitch.Answer)
def ask(run_id: str, body: Question):
    try:
        return pitch.ask(run_id, body.question)
    except (pitch.PitchUnavailable, llm.LLMError, APIError, OSError) as exc:
        raise HTTPException(
            503, "No se pudo consultar la memoria. Intenta de nuevo."
        ) from exc
