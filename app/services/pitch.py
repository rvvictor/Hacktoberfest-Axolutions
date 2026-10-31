"""Run-scoped pitch projections and source-checked Q&A."""

import asyncio
import hashlib
import importlib
import json
import os
import re
import unicodedata

from starlette.concurrency import run_in_threadpool

from app.config import settings
from app.schemas import Pitch, QAEntry, ResearchItem, Spec
from app.services import llm, research, store, voice

DEMO_RUN = "demo-pitch"
DISCLOSURE = "Soy una IA. "
NO_DATA = "no tengo ese dato"
# Words that make a question about the project as a whole, so the plan answers it when nothing else matches.
PROJECT_WORDS = {
    "proyecto", "idea", "producto", "app", "aplicacion", "sistema", "plataforma", "solucion",
    "trata", "resumen", "objetivo", "sirve", "propuesta", "speedhack",
}
# Matches every spec note the pipeline stores ("Problema: …", "Usuarios: …", "Funcionalidad del MVP: …").
PLAN_QUERY = "Problema Usuarios Funcionalidad MVP"
PLAN_ORDER = ("Problema:", "Usuarios:", "Funcionalidad del MVP:")  # what the project is, for whom, then what it does
SCRIPT_SENTENCES = (2, 4)
SENTENCE_END = re.compile(r"(?<=[.!?])\s+")
CAPITALIZED = re.compile(r"\b[A-ZÁÉÍÓÚÑ][\wÁÉÍÓÚÑáéíóúñ]+")
DOMAIN = re.compile(r"\b[\w-]+(?:\.[\w-]+)*\.(?:com|org|net|io|ai|app|co|mx|es|dev)\b", re.IGNORECASE)
DEMO_PASSAGES = [
    {
        "run_id": DEMO_RUN,
        "kind": "spec",
        "source": "demo:spec",
        "text": "El proyecto de control de gastos corporativos incluye registro con comprobante, aprobación por rol y alertas automáticas al superar un límite.",
        "demo_data": True,
    }
] + [
    # The recorded research of the demo case, so the recorded deck cites this sample's own evidence.
    {"run_id": DEMO_RUN, "kind": "research", "source": item.url, "text": item.model_dump_json(), "demo_data": True}
    for item in research._items(json.loads(research.RECORDED.read_text(encoding="utf-8")))
]
DEMO_IDEA = "SaaS de control de gastos corporativos con React, Supabase y alertas automatizadas"  # IDEA.md §3
MAX_BULLETS = 4


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



# Words that only ask (how much, who, where) and the ways to ask for a price, folded into one term.
QUESTION_WORDS = {"cuanto", "cuanta", "cuantos", "cuantas", "quien", "quienes", "donde", "cuando", "hay"}
PRICE_WORDS = {"precio", "precios", "cuesta", "cuestan", "costo", "costos", "cobra", "cobran", "tarifa", "tarifas"}


def _terms(text):
    return {"precio" if w in PRICE_WORDS else w for w in _words(text) - QUESTION_WORDS}


def _relevant(question, text):
    """Most of what the question is about appears in the passage: one shared word ("precio") is not enough."""
    asked = _terms(question)
    return bool(asked) and 2 * len(asked & _terms(text)) > len(asked)


def _stems(text):
    return {t[:5] for t in _terms(text) if len(t) >= 4}


def _grounded(answer, texts):
    """The answer names no figure, name or domain its cited passages lack, and shares their subject (a word stem)."""
    material = "\n".join(texts)
    if llm._numbers(answer) - llm._numbers(material):
        return False
    known = set(re.findall(r"\w+", _fold(material)))
    for sentence in (s for s in SENTENCE_END.split(answer) if s.strip()):
        # A capitalized word that opens a sentence may just be grammar; anywhere else it is a name.
        names = CAPITALIZED.findall(sentence)[(1 if CAPITALIZED.match(sentence) else 0) :]
        if any(_fold(word) not in known for word in names):
            return False
    if any(_fold(d) not in _fold(material) for d in DOMAIN.findall(answer)):
        return False
    stated = _stems(answer)
    return not stated or bool(stated & _stems(material))


def _provenance(run_id):
    """Demo flag of each source as the run recorded it; memory alone cannot tell a real passage from a demo one."""
    try:
        events = store.list_events(run_id)
    except Exception:  # noqa: BLE001  (no store for this run: keep memory's own flag)
        return {}
    flags = {}
    for _, e in events:
        if e.type.value == "research_item" and isinstance(e.payload.get("url"), str):
            flags[e.payload["url"]] = e.demo_data or bool(e.payload.get("demo_data"))
        elif e.type.value == "spec_ready":
            flags[f"spec:v{e.payload.get('version')}"] = e.demo_data or bool(e.payload.get("demo_data"))
    return flags

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


def cover_name(idea):
    """A short title from the idea as typed: up to its first comma or "con", at most 60 characters."""
    name = re.split(r",| con ", idea.strip(), maxsplit=1)[0].strip()
    if len(name) > 60:
        name = name[:59].rstrip() + "…"
    return name[:1].upper() + name[1:]


def _idea(run_id):
    if run_id == DEMO_RUN:
        return DEMO_IDEA
    run = store.get_run(run_id)
    return store.get_project(run.project_id).idea if run else ""


def _cover(run_id, spec, sources):
    """Slide 0: the project's name and one line, the first sentence of the plan's problem."""
    line = re.split(r"(?<=[.!?])\s+", spec.problem.strip(), maxsplit=1)[0]
    if len(line) > 160:
        line = line[:159].rstrip() + "…"
    return {"title": cover_name(_idea(run_id)) or "Tu proyecto", "bullets": [line], "sources": sources}


def _cited(slides, allowed):
    """Sources only from this run's research and plan; a slide that loses every source it had is dropped."""
    kept = []
    for s in slides:
        sources = [src for src in s.sources if src in allowed]
        if s.sources and not sources:
            continue
        kept.append({"title": s.title, "bullets": s.bullets[:MAX_BULLETS], "sources": sources})
    return kept


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
    spec, spec_sources = None, []
    for passage in passages:
        if passage.get("kind") == "spec":
            try:
                spec = Spec.model_validate_json(passage["text"])
                spec_sources = [passage["source"]]
                break
            except ValueError:
                continue
    if spec is None:
        plan = [p for p in passages if p.get("kind") == "spec"] or passages
        spec = Spec(
            version=1,
            problem="\n".join(p["text"] for p in plan),
            users=[],
            mvp_features=[],
            demo_data=any(p.get("demo_data") for p in passages),
        )
        spec_sources = list(dict.fromkeys(p["source"] for p in plan))
    found = []
    for passage in passages:
        if passage.get("kind") == "research":
            try:
                found.append(ResearchItem.model_validate_json(passage["text"]))
            except ValueError:
                continue
    allowed = {r.url for r in found} | set(spec_sources)
    cover = _cover(run_id, spec, spec_sources)
    if llm._demo() and not found:
        # Nothing researched to show: the plan's features, with the plan as the source.
        proposal = {"title": "La propuesta", "bullets": (spec.mvp_features or ["Pregúntale a la memoria del proyecto."])[
            :MAX_BULLETS], "sources": spec_sources}
        return Pitch(slides=[cover, proposal], demo_data=True)
    # In demo, build_deck returns the recorded deck of the demo case; it is shown only with that run's research.
    result = llm.build_deck(spec, found)
    return Pitch(
        slides=[cover, *_cited(result.slides, allowed)],
        demo_data=result.demo_data or spec.demo_data or any(p.get("demo_data") for p in passages),
    )

def ask(run_id, question):
    question = question.strip()
    records = recall(run_id, question)
    records = [
        p
        for p in records
        if p.get("run_id") == run_id
        and p.get("source")
        and _relevant(question, p.get("text", ""))
    ]
    if not records and _words(question) & PROJECT_WORDS:
        # A general question about the project ("¿de qué trata el proyecto?") shares no word with any passage:
        # answer from the plan's notes (problem, users, features). Any other unmatched question stays NO_DATA.
        records = sorted(
            (
                p
                for p in recall(run_id, PLAN_QUERY, k=10)
                if p.get("run_id") == run_id and p.get("source") and p.get("kind") == "spec_note"
            ),
            key=lambda p: next((n for n, head in enumerate(PLAN_ORDER) if p["text"].startswith(head)), len(PLAN_ORDER)),
        )
    # Pipeline runs store readable notes next to the raw spec JSON; quote a note, never the JSON.
    notes = [p for p in records if p.get("kind") in ("spec_note", "research_note")]
    quotable = bool(notes) and settings.DEMO_MODE
    if quotable:
        records = notes
    flags = _provenance(run_id)
    passages = [llm.Passage(text=p["text"], source=p["source"]) for p in records]
    entry = (
        llm.answer(question, passages)
        if passages
        else QAEntry(question=question, answer=NO_DATA)
    )
    allowed = {p.source for p in passages}
    valid = bool(entry.sources) and set(entry.sources) <= allowed
    if valid and not settings.DEMO_MODE:
        # A model answer must say what its cited passages say, not only cite them.
        valid = _grounded(entry.answer, [p.text for p in passages if p.source in entry.sources])
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
        quoted = passages[:3] if quotable else passages[:1]
        entry = QAEntry(
            question=question,
            answer="Según la memoria de demostración: " + " ".join(p.text for p in quoted),
            sources=list(dict.fromkeys(p.source for p in quoted)),
        )
        valid = True
    if not valid or explicit_no_data:
        entry = QAEntry(question=question, answer=NO_DATA)
    # Demo when the model is the recorded one, or any passage the answer relies on is recorded or demo.
    used = [p for p in records if p["source"] in entry.sources] or records
    demo = llm._demo() or any(flags.get(p["source"], p.get("demo_data")) for p in used)
    return Answer(
        question=question,
        answer=DISCLOSURE + entry.answer,
        sources=entry.sources,
        demo_data=demo,
    )


def _fold(text):
    plain = unicodedata.normalize("NFKD", text.casefold())
    return "".join(c for c in plain if not unicodedata.combining(c))


def validate_script(script, slide):
    """A spoken script may only say what its slide says: 2-4 sentences, no figure, name or domain the slide lacks."""
    if not isinstance(script, str):
        raise TypeError("script must be a string")
    script = script.strip()
    sentences = [s for s in SENTENCE_END.split(script) if s.strip()]
    low, high = SCRIPT_SENTENCES
    if not low <= len(sentences) <= high:
        raise ValueError(f"script has {len(sentences)} sentences; it needs {low} to {high}")
    material = "\n".join([slide.title, *slide.bullets, *slide.sources])
    extra = llm._numbers(script) - llm._numbers(material)
    if extra:
        raise ValueError(f"script has figures not on the slide: {sorted(extra)}")
    known = set(re.findall(r"\w+", _fold(material)))
    # A capitalized word that opens a sentence may just be grammar; anywhere else it is a name.
    names = [
        word
        for sentence in sentences
        for word in CAPITALIZED.findall(sentence)[(1 if CAPITALIZED.match(sentence) else 0) :]
        if _fold(word) not in known
    ]
    if names:
        raise ValueError(f"script has names not on the slide: {', '.join(dict.fromkeys(names))}")
    domains = [d for d in DOMAIN.findall(script) if _fold(d) not in _fold(material)]
    if domains:
        raise ValueError(f"script has names not on the slide: {', '.join(domains)}")
    return script


def _recorded_script(slide):
    """The demo narration is the slide read aloud: nothing it says can be absent from the slide."""
    parts = [slide.title, *slide.bullets[:3]]
    if len(parts) < SCRIPT_SENTENCES[0]:
        parts.append("Esta es la idea principal de la diapositiva")
    return ". ".join(p.strip().rstrip(".!?") for p in parts) + "."


def narration_script(slide):
    if llm._demo():
        return _recorded_script(slide)
    user = llm._data("slide", slide.model_dump(mode="json"))
    return llm._run("narration", user, lambda data: validate_script(data["script"], slide))


def _run_dir(kind, run_id):
    return settings.DATA_DIR / kind / hashlib.sha256(run_id.encode()).hexdigest()[:16]


def remember_deck(run_id, result):
    """Keep the deck a run was last shown: narration speaks only slides the server itself served."""
    path = _run_dir("pitch", run_id) / "deck.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    _write(path, result.model_dump_json().encode())


def served_slide(run_id, index):
    try:
        slides = Pitch.model_validate_json((_run_dir("pitch", run_id) / "deck.json").read_text()).slides
    except (OSError, ValueError):
        return None
    return slides[index] if 0 <= index < len(slides) else None


def _write(path, data):
    tmp = path.with_name(f"{path.name}.{os.getpid()}.tmp")
    tmp.write_bytes(data)
    os.replace(tmp, path)


NARRATION_SLOTS = asyncio.Semaphore(2)  # each miss costs an LLM call and a paid TTS call
NARRATION_LOCKS = {}  # one lock per audio key: concurrent misses for a slide pay once


async def narrate(run_id, index):
    """Audio for one served slide, generated once per run and cached; slide 0 opens with the AI disclosure.

    Returns None when the run has no served deck or the index is outside it."""
    slide = served_slide(run_id, index)
    if slide is None:
        return None
    if voice.recorded():
        return (voice.FIXTURES / "tts.mp3").read_bytes(), True
    demo = llm._demo()
    voice_id = settings.ELEVENLABS_VOICE_ID or ""
    key = hashlib.sha256(f"{voice_id}|{index == 0}|{demo}|{slide.model_dump_json()}".encode()).hexdigest()[:32]
    path = _run_dir("narration", run_id) / f"{key}.mp3"
    if path.exists():
        return path.read_bytes(), demo
    lock = NARRATION_LOCKS.setdefault(key, asyncio.Lock())
    async with lock:
        if path.exists():  # a concurrent request for this slide already paid for it
            return path.read_bytes(), demo
        if not demo:
            voice.check_budget()
        async with NARRATION_SLOTS:
            script = await run_in_threadpool(narration_script, slide)
            audio = await voice.synthesize(voice.with_disclosure(script) if index == 0 else script)
        path.parent.mkdir(parents=True, exist_ok=True)
        _write(path, audio)
        NARRATION_LOCKS.pop(key, None)
    return audio, demo
