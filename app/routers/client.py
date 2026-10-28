"""Client mode (Doña Lupe's barbershop). Everything is a recorded fixture: demo_data is always true."""

import json
from pathlib import Path
from typing import Literal

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(prefix="/api/client", tags=["client"])

FIXTURE = Path(__file__).resolve().parent.parent / "fixtures" / "client" / "journey.json"


class Business(BaseModel):
    name: str
    owner: str
    place: str
    note: str


class Question(BaseModel):
    id: str
    question: str
    answer: str


class Summary(BaseModel):
    headline: str
    points: list[str]


class Screen(BaseModel):
    id: str
    title: str
    description: str


class ProgressStep(BaseModel):
    id: str
    title: str
    state: Literal["done", "current", "next"]


class Progress(BaseModel):
    percent: int
    steps: list[ProgressStep]


class WhatsAppPreview(BaseModel):
    to_name: str
    message: str
    opt_in: str
    opt_out: str
    sent: bool


class PublishedApp(BaseModel):
    url: str
    note: str


class AudioGuide(BaseModel):
    title: str
    duration_seconds: int
    src: str | None
    recorded_path: str
    recorded: bool
    note: str
    transcript: list[str]


class Journey(BaseModel):
    demo_data: bool
    business: Business
    questions: list[Question]
    summary: Summary
    screens: list[Screen]
    progress: Progress
    whatsapp: WhatsAppPreview
    published_app: PublishedApp
    audio_guide: AudioGuide


def load_journey() -> Journey:
    return Journey.model_validate(json.loads(FIXTURE.read_text(encoding="utf-8")))


@router.get("/journey", response_model=Journey)
def get_journey() -> Journey:
    return load_journey()
