from .content import (  # noqa: F401
    Architecture,
    BacklogItem,
    MiroItem,
    Pitch,
    Prospect,
    Prototype,
    QAEntry,
    QualityCheck,
    QualityReport,
    ResearchItem,
    Slide,
    Spec,
)
from .run import (  # noqa: F401
    STAGES,
    Approval,
    ApprovalState,
    EventType,
    Mode,
    Project,
    Run,
    RunStatus,
    StageEvent,
)

# Entity validated by `StageEvent.payload` for each event type that carries one.
PAYLOAD_MODELS = {
    EventType.research_item: ResearchItem,
    EventType.spec_ready: Spec,
    EventType.miro_item: MiroItem,
    EventType.linear_issue: BacklogItem,
    EventType.prototype_ready: Prototype,
    EventType.pitch_ready: Pitch,
}
