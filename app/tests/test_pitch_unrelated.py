"""A question the project does not cover gets "no tengo ese dato", even if it shares one word with a note (HACK-061)."""

import pytest

from app.config import settings
from app.schemas import QAEntry
from app.services import pitch
from app.tests.test_pipeline import _approve, _create, _events, client  # noqa: F401  (client is a fixture)

DOLLAR = "¿Cuál es el precio del dólar hoy?"
COMPETITOR_PRICE = "¿Cuánto cuesta la competencia?"
ALERTS = "¿Cómo funcionan las alertas?"


def _finished_run(client):  # noqa: F811  (pytest fixture imported above)
    run_id = _create(client)
    client.post(f"/api/runs/{run_id}/answers", json={"answers": ["a", "b", "c"]})
    for n in (1, 2, 3):
        _approve(client, run_id, n)
    return run_id


def _ask(client, run_id, question):  # noqa: F811
    return client.post(f"/api/pitch/{run_id}/ask", json={"question": question}).json()


def test_demo_dollar_question_has_no_data(client):  # noqa: F811
    run_id = _finished_run(client)
    answer = _ask(client, run_id, DOLLAR)
    assert answer["answer"].endswith(pitch.NO_DATA) and answer["sources"] == []


def test_demo_competitor_price_still_cites_research(client):  # noqa: F811
    run_id = _finished_run(client)
    research_urls = {e["payload"]["url"] for e in _events(client, run_id) if e["type"] == "research_item"}
    answer = _ask(client, run_id, COMPETITOR_PRICE)
    assert pitch.NO_DATA not in answer["answer"]
    assert answer["sources"] and set(answer["sources"]) <= research_urls


def test_demo_alerts_question_still_answers(client):  # noqa: F811
    run_id = _finished_run(client)
    answer = _ask(client, run_id, ALERTS)
    assert pitch.NO_DATA not in answer["answer"] and answer["sources"]


NOTES = [
    {"run_id": "run_live0001", "kind": "research_note", "source": "https://rival.test/pricing",
     "text": "Competidores y competencia: Rival. Precio: $75/month. Funciones: reportes"},
    {"run_id": "run_live0001", "kind": "spec_note", "source": "spec:v1",
     "text": "Funcionalidad del MVP: Alertas automatizadas por correo electrónico"},
]


@pytest.fixture
def live(monkeypatch):
    """A live run with the LLM stubbed: it cites every passage it is given, as a careless model would."""
    monkeypatch.setattr(settings, "DEMO_MODE", False)
    monkeypatch.setattr(pitch, "recall", lambda run, query, k=5: [dict(p) for p in NOTES])
    given = []

    def answer(question, passages):
        given.append([p.source for p in passages])
        return QAEntry(question=question, answer=" ".join(p.text for p in passages), sources=[p.source for p in passages])

    monkeypatch.setattr(pitch.llm, "answer", answer)
    return given


@pytest.mark.parametrize("question", [DOLLAR, "¿Precio del dólar?"])
def test_live_dollar_question_never_reaches_the_model(live, question):
    result = pitch.ask("run_live0001", question)
    assert result.answer.endswith(pitch.NO_DATA) and result.sources == [] and live == []


def test_live_competitor_price_gets_only_the_research_note(live):
    result = pitch.ask("run_live0001", COMPETITOR_PRICE)
    assert live == [["https://rival.test/pricing"]] and result.sources == ["https://rival.test/pricing"]


def test_live_alerts_question_gets_only_the_plan_note(live):
    result = pitch.ask("run_live0001", ALERTS)
    assert live == [["spec:v1"]] and result.sources == ["spec:v1"]
