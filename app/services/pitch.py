"""Run-scoped pitch projections and source-checked Q&A."""

import importlib
import re
import unicodedata

from app.config import settings
from app.schemas import Pitch, QAEntry, ResearchItem, Spec
from app.services import llm

DEMO_RUN = "demo-pitch"
DISCLOSURE = "Soy una IA. "
NO_DATA = "no tengo ese dato"
DEMO_PASSAGES = [
    {
        "run_id": DEMO_RUN,
        "kind": "spec",
        "source": "demo:spec",
        "text": "El proyecto de control de gastos corporativos incluye registro con comprobante, aprobación por rol y alertas automáticas al superar un límite.",
        "demo_data": True,
    }
]


class PitchUnavailable(Exception):
    pass


class Answer(QAEntry):
    demo_data: bool = False


def _words(text):
    plain = unicodedata.normalize("NFKD", text.casefold())
    words = set(
        re.findall(r"\w+", "".join(c for c in plain if not unicodedata.combining(c)))
    )
    return words - {
        "que",
        "cual",
        "cuales",
        "como",
        "por",
        "para",
        "del",
        "las",
        "los",
        "una",
        "uno",
        "unos",
        "con",
        "son",
        "tiene",
        "tengo",
        "dato",
        "ese",
        "funcionan",
        "funciona",
        "explica",
        "es",
        "el",
        "la",
        "de",
        "en",
        "y",
        "se",
        "al",
        "mi",
        "me",
        "un",
        "su",
        "a",
    }


def recall(run_id, query, k=5):
    """Use the memory contract; only the named demo run has local sample data."""
    if run_id == DEMO_RUN and settings.DEMO_MODE:
        return [dict(p) for p in DEMO_PASSAGES if _words(query) & _words(p["text"])][:k]
    try:
        memory = importlib.import_module("app.services.memory")
    except ModuleNotFoundError as exc:
        if exc.name != "app.services.memory":
            raise
        raise PitchUnavailable(
            "La memoria aún no está disponible para esta ejecución."
        ) from exc
    return memory.recall(run_id, query, k=k)


def deck(run_id):
    passages = recall(
        run_id,
        "spec proyecto problema usuarios funciones arquitectura investigación "
        "version problem users mvp_features competitor pricing features",
        k=50,
    )
    passages = [p for p in passages if p.get("run_id") == run_id]
    if not passages:
        return Pitch(slides=[])
    # The stored spec is authoritative; never substitute another run's sample spec.
    spec = None
    for passage in passages:
        if passage.get("kind") == "spec":
            try:
                spec = Spec.model_validate_json(passage["text"])
                break
            except ValueError:
                continue
    if spec is None:
        spec = Spec(
            version=1,
            problem="\n".join(p["text"] for p in passages),
            users=[],
            mvp_features=[],
            demo_data=any(p.get("demo_data") for p in passages),
        )
    if llm._demo():
        # The provider's fixed deck fixture belongs to a different input; project
        # this run's actual evidence instead, with explicit demo provenance.
        return Pitch(
            slides=[
                {
                    "title": "El proyecto",
                    "bullets": [spec.problem],
                    "sources": [p["source"] for p in passages],
                },
                {
                    "title": "La propuesta",
                    "bullets": spec.mvp_features
                    or ["Pregúntale a la memoria del proyecto."],
                    "sources": spec.sources or [p["source"] for p in passages],
                },
            ],
            demo_data=True,
        )
    research = []
    for passage in passages:
        if passage.get("kind") == "research":
            try:
                research.append(ResearchItem.model_validate_json(passage["text"]))
            except ValueError:
                continue
    result = llm.build_deck(spec, research)
    return result.model_copy(
        update={
            "demo_data": result.demo_data
            or spec.demo_data
            or any(p.get("demo_data") for p in passages)
        }
    )


def ask(run_id, question):
    question = question.strip()
    records = recall(run_id, question)
    records = [
        p
        for p in records
        if p.get("run_id") == run_id
        and p.get("source")
        and _words(question) & _words(p.get("text", ""))
    ]
    # Pipeline runs store readable notes next to the raw spec JSON; quote a note, never the JSON.
    notes = [p for p in records if p.get("kind") == "spec_note"]
    quotable = bool(notes) and settings.DEMO_MODE
    if quotable:
        records = notes
    demo = llm._demo() or any(p.get("demo_data") for p in records)
    passages = [llm.Passage(text=p["text"], source=p["source"]) for p in records]
    entry = (
        llm.answer(question, passages)
        if passages
        else QAEntry(question=question, answer=NO_DATA)
    )
    allowed = {p.source for p in passages}
    valid = bool(entry.sources) and set(entry.sources) <= allowed
    explicit_no_data = entry.answer.strip().lower().rstrip(".") == NO_DATA
    if (
        settings.DEMO_MODE
        and (run_id == DEMO_RUN or quotable)
        and passages
        and not valid
        and not explicit_no_data
        and (quotable or _words(question) <= _words(passages[0].text))
    ):
        # Recorded LLM answers may describe a different fixture. Quote this
        # demo's evidence verbatim instead of presenting that unrelated answer.
        entry = QAEntry(
            question=question,
            answer="Según la memoria de demostración: " + passages[0].text,
            sources=[passages[0].source],
        )
        valid = True
    if not valid or explicit_no_data:
        entry = QAEntry(question=question, answer=NO_DATA)
    return Answer(
        question=question,
        answer=DISCLOSURE + entry.answer,
        sources=entry.sources,
        demo_data=demo,
    )
