"""Pitch Q&A on a real run: real passages are not labeled demo, competitors are found, answers are grounded (HACK-067)."""

import time

import pytest

from app.config import settings
from app.schemas import EventType, Mode, QAEntry, StageEvent
from app.services import llm, memory, pipeline, pitch, store

SPEC = {
    "version": 1,
    "problem": "Los clientes de un negocio de bombas de agua y motores no ven los productos ni los precios, "
               "y las cotizaciones se piden por teléfono y se pierden entre los mensajes del día.",
    "users": ["Dueño del negocio", "Clientes que compran bombas y motores"],
    "mvp_features": ["Catálogo de productos con fichas técnicas", "Solicitud de cotización en línea",
                     "Panel para responder las cotizaciones", "Alertas de nuevas cotizaciones"],
    "assumptions": ["Los precios los carga el dueño"],
    "sources": [],
}
RIVAL = {"competitor": "Bombas Pro", "url": "https://bombaspro.test/catalogo", "pricing": "$1,200",
         "features": ["catálogo en línea", "envíos"], "demo_data": False}
OTHER = {"competitor": "Motores MX", "url": "https://motoresmx.test", "pricing": None,
         "features": ["refacciones"], "demo_data": False}
JUNK = {"competitor": "CB Insights", "url": "https://cbinsights.test/report", "pricing": None,
        "features": ["cotización para el cliente", "inteligencia de mercado"], "demo_data": False}
RECORDED = {"competitor": "Bombas Demo", "url": "https://demo.test/bombas", "pricing": None,
            "features": ["catálogo"], "demo_data": True}


@pytest.fixture
def run_id(tmp_path, monkeypatch):
    """A real (not demo) run, fed to memory the way the pipeline does it, with no Backboard key."""
    monkeypatch.setattr(settings, "DATA_DIR", tmp_path)
    monkeypatch.setattr(settings, "DEMO_MODE", False)
    monkeypatch.setattr(llm, "_demo", lambda: False)
    monkeypatch.setattr(memory, "_service", memory.MemoryService(api_key="", demo_mode=False))
    _, run = store.create_run(Mode.client, "catálogo de bombas de agua y motores", [], demo_data=False)
    for stage, etype, payload in [(3, EventType.research_item, item) for item in (RIVAL, OTHER, JUNK, RECORDED)] + [
        (4, EventType.spec_ready, SPEC)
    ]:
        payload = pipeline._record(run.run_id, stage, etype, dict(payload))
        store.add_event(StageEvent(run_id=run.run_id, stage=stage, type=etype, payload=payload, ts=time.time(),
                                   demo_data=bool(payload.get("demo_data"))))
    return run.run_id


def _model(monkeypatch, answer):
    """The LLM stubbed: it answers `answer(passages)` and cites the passages it used."""
    given = []

    def fake(question, passages):
        given.append(passages)
        text, sources = answer(passages)
        return QAEntry(question=question, answer=text, sources=sources)

    monkeypatch.setattr(llm, "answer", fake)
    return given


def test_a_competitor_question_answers_from_the_research_notes(run_id, monkeypatch):
    def answer(passages):
        notes = [p for p in passages if p.source in (RIVAL["url"], OTHER["url"])]
        return "Los competidores son Bombas Pro y Motores MX.", [p.source for p in notes]

    given = _model(monkeypatch, answer)
    result = pitch.ask(run_id, "¿Quiénes son los competidores?")
    assert {RIVAL["url"], OTHER["url"]} <= {p.source for p in given[0]}
    assert pitch.NO_DATA not in result.answer and set(result.sources) == {RIVAL["url"], OTHER["url"]}


def test_real_passages_are_not_labeled_demo(run_id, monkeypatch):
    _model(monkeypatch, lambda ps: ("Bombas Pro cobra $1,200 por su catálogo en línea.", [RIVAL["url"]]))
    result = pitch.ask(run_id, "¿Cuánto cuesta Bombas Pro?")
    assert result.sources == [RIVAL["url"]] and result.demo_data is False


def test_a_passage_from_a_recorded_item_stays_demo(run_id, monkeypatch):
    _model(monkeypatch, lambda ps: ("Bombas Demo tiene catálogo.", [RECORDED["url"]]))
    result = pitch.ask(run_id, "¿Qué ofrece Bombas Demo?")
    assert result.sources == [RECORDED["url"]] and result.demo_data is True


def test_an_answer_its_cited_passage_does_not_support_is_rejected(run_id, monkeypatch):
    _model(monkeypatch, lambda ps: ("El cliente pide la cotización por WhatsApp en minutos.", [JUNK["url"]]))
    result = pitch.ask(run_id, "¿Cómo pide una cotización el cliente?")
    assert result.answer.endswith(pitch.NO_DATA) and result.sources == []
