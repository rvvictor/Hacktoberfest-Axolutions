"""Entities produced along the pipeline (IDEA.md §6)."""
from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class ResearchItem(BaseModel):
    competitor: str
    pricing: Optional[str] = None
    features: List[str] = Field(default_factory=list)
    url: str = Field(min_length=1)
    fetched_at: Optional[datetime] = None
    demo_data: bool = False


class Spec(BaseModel):
    version: int = Field(ge=1)
    problem: str
    users: List[str]
    mvp_features: List[str]
    assumptions: List[str] = Field(default_factory=list)
    sources: List[str] = Field(default_factory=list)
    demo_data: bool = False


class MiroItem(BaseModel):
    kind: str  # screen | data_model | integration | connector
    title: str
    miro_id: Optional[str] = None
    x: float = 0
    y: float = 0
    demo_data: bool = False


class Architecture(BaseModel):
    screens: List[str]
    data_model: List[str]
    integrations: List[str]
    miro_board_id: Optional[str] = None
    items: List[MiroItem] = Field(default_factory=list)
    demo_data: bool = False


class BacklogItem(BaseModel):
    epic: str
    title: str
    acceptance: List[str]
    external_id: str
    linear_id: Optional[str] = None
    url: Optional[str] = None
    demo_data: bool = False


class Prototype(BaseModel):
    generator: str = Field(pattern="^(lovable|planb)$")
    url: str
    build_url: Optional[str] = None
    repo_url: Optional[str] = None
    demo_data: bool = False


class QualityCheck(BaseModel):
    name: str = Field(pattern="^(build|lint|gitleaks|rls|smoke)$")
    passed: bool
    details: str = ""


class QualityReport(BaseModel):
    checks: List[QualityCheck]
    passed: bool
    details: str = ""
    demo_data: bool = False


class Slide(BaseModel):
    title: str
    bullets: List[str] = Field(default_factory=list)
    sources: List[str] = Field(default_factory=list)


class QAEntry(BaseModel):
    question: str
    answer: str
    sources: List[str] = Field(default_factory=list)


class Pitch(BaseModel):
    slides: List[Slide]
    qa_log: List[QAEntry] = Field(default_factory=list)
    demo_data: bool = False


class Prospect(BaseModel):
    business: str
    public_info: str
    draft_message: str
    approved_by: Optional[str] = None
    opt_out: bool = False
    consent: bool = False
    demo_data: bool = True
