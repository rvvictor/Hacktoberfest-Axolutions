"""HACK-075: the research-query prompt asks for competing businesses, never the idea's own words alone.

No network: the model call is stubbed and only the prompt it receives is inspected.
"""
import json
import re

import pytest

from app.schemas import Mode
from app.services import llm, stages

PUMPS = "negocio de catálogo de productos de bombas de agua y motores"
ANSWERS = {"¿Para quién?": "ferreterías de Jalisco"}


@pytest.fixture(autouse=True)
def live(monkeypatch):
    monkeypatch.setattr(llm.settings, "DEMO_MODE", False)
    monkeypatch.setattr(llm.settings, "ANTHROPIC_API_KEY", "test-key")
    monkeypatch.setattr(llm.settings, "LLM_MODEL", "claude-sonnet-5-5")
    monkeypatch.setattr(llm.gemini_env, "GEMINI_API_KEY", None)


def stub(monkeypatch, *replies):
    seen, queue = [], list(replies)

    def fake(system, user, **_):
        seen.append((system, user))
        r = queue.pop(0)
        return r if isinstance(r, str) else json.dumps(r)

    monkeypatch.setattr(llm, "_complete", fake)
    return seen


def test_prompt_asks_for_competing_businesses_and_their_software(monkeypatch):
    seen = stub(monkeypatch, {"queries": ["tienda en línea de bombas de agua"]})
    llm.research_queries(PUMPS, Mode.client, ANSWERS)
    system = seen[0][0].lower()
    assert "negocios" in system and "mismo" in system  # other businesses that sell the same thing
    assert "en línea" in system and "software" in system  # ...online, and the software they would use
    for bait in ("catálogo", "pdf", "directorio"):  # the failure mode is named so the model avoids it
        assert bait in system
    assert "solo con las palabras de la idea" in system or "palabras de la idea" in system


def test_idea_travels_only_inside_its_data_block(monkeypatch):
    seen = stub(monkeypatch, {"queries": ["tienda en línea de bombas de agua"]})
    llm.research_queries(PUMPS, Mode.client, ANSWERS)
    system, user = seen[0]
    assert PUMPS not in system and "bombas" not in system  # prompt examples are not the idea's words
    blocks = re.findall(r'<data name="idea">\n(.*?)\n</data>', user, re.DOTALL)
    assert blocks == [PUMPS]
    assert user.count(PUMPS) == 1


@pytest.mark.parametrize("queries", [["a competing shop"], ["q one", "q two", "q three"]])
def test_one_to_three_queries_are_accepted(monkeypatch, queries):
    stub(monkeypatch, {"queries": queries})
    assert llm.research_queries(PUMPS, Mode.client, ANSWERS) == queries


@pytest.mark.parametrize("queries", [[], ["a", "b", "c", "d"]])
def test_other_counts_are_rejected_after_one_retry(monkeypatch, queries):
    seen = stub(monkeypatch, {"queries": queries}, {"queries": queries})
    with pytest.raises(llm.LLMOutputError):
        llm.research_queries(PUMPS, Mode.client, ANSWERS)
    assert len(seen) == 2


def test_failure_still_falls_back_to_the_idea(monkeypatch):
    stub(monkeypatch, "no es json", "tampoco")
    assert stages._research_queries(PUMPS, Mode.client, ANSWERS) == [PUMPS]
