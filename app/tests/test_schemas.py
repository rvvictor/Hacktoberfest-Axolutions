import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

import pytest
from pydantic import ValidationError

from app.schemas import PAYLOAD_MODELS, EventType, ResearchItem, Run, StageEvent

FIXTURE = ROOT / "app" / "fixtures" / "demo" / "run.jsonl"


def load():
    return [json.loads(line) for line in FIXTURE.read_text().splitlines() if line.strip()]


def test_every_line_validates_and_payload_matches_entity():
    lines = load()
    assert lines
    for raw in lines:
        ev = StageEvent(**raw)
        model = PAYLOAD_MODELS.get(ev.type)
        if model:
            model(**ev.payload)
        assert ev.demo_data is True


def test_enum_covers_whole_flow():
    assert {e.value for e in EventType} == {
        "stage_started", "stage_done", "question", "research_item", "spec_ready",
        "approval_required", "approval_given", "approval_rejected", "miro_item",
        "linear_issue", "prototype_ready", "quality_check", "pitch_ready", "error",
    }


def test_fixture_is_a_complete_run():
    evs = [StageEvent(**r) for r in load()]
    c = Counter(e.type for e in evs)
    assert {e.stage for e in evs if e.type == EventType.stage_started} == set(range(1, 10))
    assert c[EventType.approval_given] == 3
    assert c[EventType.miro_item] >= 12
    assert c[EventType.linear_issue] >= 6  # the recorded backlog (HACK-054 decision)
    ts = [e.ts for e in evs]
    assert ts == sorted(ts)


def test_research_item_requires_url_and_run_has_three_approvals():
    with pytest.raises(ValidationError):
        ResearchItem(competitor="x", url="")
    assert len(Run(run_id="r", project_id="p", stage=1).approvals) == 3
