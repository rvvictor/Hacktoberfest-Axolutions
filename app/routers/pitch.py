from anthropic import APIError
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field, field_validator

from app.schemas import Pitch
from app.services import llm, pitch

router = APIRouter(prefix="/api/pitch", tags=["pitch"])


class Question(BaseModel):
    question: str = Field(min_length=1, max_length=2000)

    @field_validator("question")
    @classmethod
    def nonempty(cls, value):
        if not value.strip():
            raise ValueError("Escribe una pregunta")
        return value.strip()


@router.get("/{run_id}", response_model=Pitch)
def get_deck(run_id: str):
    try:
        return pitch.deck(run_id)
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
