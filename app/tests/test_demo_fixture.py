"""The demo replay shows the real recorded research (HACK-025), labeled demo, never placeholders."""

import json
from pathlib import Path

from app.services import research

RUN = Path(__file__).parents[1] / "fixtures" / "demo" / "run.jsonl"


def _events():
    return [json.loads(line) for line in RUN.read_text(encoding="utf-8").splitlines() if line.strip()]


def test_replay_research_is_the_real_recording():
    recorded = {r["url"] for r in json.loads(research.RECORDED.read_text(encoding="utf-8"))["results"] if r.get("url")}
    items = [e["payload"] for e in _events() if e["type"] == "research_item"]
    assert len(items) >= 3
    assert all(i["url"].startswith("https://") and i["url"] in recorded for i in items)
    assert all(i["demo_data"] is True for i in items)


def test_replay_spec_cites_only_that_research():
    events = _events()
    urls = {e["payload"]["url"] for e in events if e["type"] == "research_item"}
    spec = next(e["payload"] for e in events if e["type"] == "spec_ready")
    assert spec["sources"] and set(spec["sources"]) <= urls and spec["demo_data"] is True


def test_replay_has_no_placeholders():
    text = RUN.read_text(encoding="utf-8")
    assert "example.invalid" not in text and "Placeholder" not in text
