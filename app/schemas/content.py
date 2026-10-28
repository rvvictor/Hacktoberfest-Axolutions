"""Entities produced along the pipeline (IDEA.md §6)."""
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class ResearchItem(BaseModel):
    competitor: str
    pricing: str | None = None
    features: list[str] = Field(default_factory=list)
    url: str = Field(min_length=1)
    fetched_at: datetime | None = None
    demo_data: bool = False


class Spec(BaseModel):
    version: int = Field(ge=1)
    problem: str
    users: list[str]
    mvp_features: list[str]
    assumptions: list[str] = Field(default_factory=list)
    sources: list[str] = Field(default_factory=list)
    demo_data: bool = False


class MiroItem(BaseModel):
    kind: str  # screen | data_model | integration | connector
    title: str
    miro_id: str | None = None
    x: float = 0
    y: float = 0
    demo_data: bool = False


class Architecture(BaseModel):
    screens: list[str]
    data_model: list[str]
    integrations: list[str]
    miro_board_id: str | None = None
    items: list[MiroItem] = Field(default_factory=list)
    demo_data: bool = False


class BacklogItem(BaseModel):
    epic: str
    title: str
    acceptance: list[str]
    external_id: str
    linear_id: str | None = None
    url: str | None = None
    demo_data: bool = False


class Prototype(BaseModel):
    generator: str = Field(pattern="^(lovable|planb)$")
    url: str
    build_url: str | None = None
    repo_url: str | None = None
    demo_data: bool = False


class QualityCheck(BaseModel):
    name: str = Field(pattern="^(build|lint|gitleaks|rls|smoke)$")
    passed: bool
    details: str = ""


class QualityReport(BaseModel):
    checks: list[QualityCheck]
    passed: bool
    details: str = ""
    demo_data: bool = False


class Slide(BaseModel):
    title: str
    bullets: list[str] = Field(default_factory=list)
    sources: list[str] = Field(default_factory=list)


class QAEntry(BaseModel):
    question: str
    answer: str
    sources: list[str] = Field(default_factory=list)


class Pitch(BaseModel):
    slides: list[Slide]
    qa_log: list[QAEntry] = Field(default_factory=list)
    demo_data: bool = False


class Prospect(BaseModel):
    business: str
    public_info: str
    draft_message: str
    approved_by: str | None = None
    opt_out: bool = False
    consent: bool = False
    demo_data: bool = True
