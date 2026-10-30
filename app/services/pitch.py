"""Run-scoped pitch projections and source-checked Q&A."""

import hashlib
import importlib
import re
import unicodedata

from app.config import settings
from app.schemas import Pitch, QAEntry, ResearchItem, Spec
from app.services import llm, voice

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
        quoted = passages[:3] if quotable else passages[:1]
        entry = QAEntry(
            question=question,
            answer="Según la memoria de demostración: " + " ".join(p.text for p in quoted),
            sources=list(dict.fromkeys(p.source for p in quoted)),
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


def _fold(text):
    plain = unicodedata.normalize("NFKD", text.casefold())
    return "".join(c for c in plain if not unicodedata.combining(c))


def validate_script(script, slide):
    """A spoken script may only say what its slide says: 2-4 sentences, no figure, name or domain the slide lacks."""
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


def _audio_path(run_id, key):
    run = hashlib.sha256(run_id.encode()).hexdigest()[:16]
    return settings.DATA_DIR / "narration" / run / f"{key}.mp3"


async def narrate(run_id, index, slide):
    """Audio for one slide, generated once per run and cached; the first slide opens with the AI disclosure."""
    from starlette.concurrency import run_in_threadpool

    if voice.recorded():
        return (voice.FIXTURES / "tts.mp3").read_bytes(), True
    voice_id = settings.ELEVENLABS_VOICE_ID or ""
    key = hashlib.sha256(f"{voice_id}|{index == 0}|{slide.model_dump_json()}".encode()).hexdigest()[:32]
    path = _audio_path(run_id, key)
    demo = llm._demo()
    if path.exists():
        return path.read_bytes(), demo
    script = await run_in_threadpool(narration_script, slide)
    audio = await voice.synthesize(voice.with_disclosure(script) if index == 0 else script)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(audio)
    return audio, demo
