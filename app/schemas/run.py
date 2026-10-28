"""Project, Run and StageEvent: the run contract shared by backend, SSE and web."""
from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class Mode(str, Enum):
    dev = "dev"
    client = "client"


class RunStatus(str, Enum):
    pending = "pending"
    running = "running"
    awaiting_approval = "awaiting_approval"
    done = "done"
    failed = "failed"


class ApprovalState(str, Enum):
    pending = "pending"
    approved = "approved"
    rejected = "rejected"


class EventType(str, Enum):
    stage_started = "stage_started"
    stage_done = "stage_done"
    question = "question"
    research_item = "research_item"
    spec_ready = "spec_ready"
    approval_required = "approval_required"
    approval_given = "approval_given"
    approval_rejected = "approval_rejected"
    miro_item = "miro_item"
    linear_issue = "linear_issue"
    prototype_ready = "prototype_ready"
    quality_check = "quality_check"
    pitch_ready = "pitch_ready"
    error = "error"


STAGES = {
    1: "intake",
    2: "clarify",
    3: "research",
    4: "spec",
    5: "architecture",
    6: "backlog",
    7: "prototype",
    8: "quality",
    9: "pitch",
}


class Project(BaseModel):
    id: str
    mode: Mode
    idea: str
    stack_prefs: list[str] = Field(default_factory=list)
    demo_data: bool = False


class Approval(BaseModel):
    number: int = Field(ge=1, le=3)
    state: ApprovalState = ApprovalState.pending
    decided_by: str | None = None


class Run(BaseModel):
    run_id: str
    project_id: str
    stage: int = Field(ge=1, le=9)
    status: RunStatus = RunStatus.pending
    approvals: list[Approval] = Field(
        default_factory=lambda: [Approval(number=n) for n in (1, 2, 3)],
        min_length=3,
        max_length=3,
    )
    cost_by_step: dict[str, float] = Field(default_factory=dict)
    demo_data: bool = False


class StageEvent(BaseModel):
    """One SSE event. `ts` is seconds since the run started (relative, for replay)."""

    run_id: str
    stage: int = Field(ge=1, le=9)
    type: EventType
    payload: dict[str, Any] = Field(default_factory=dict)
    ts: float = Field(ge=0)
    demo_data: bool = False
