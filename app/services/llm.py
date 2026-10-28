"""LLM service: clarification, spec, architecture, backlog, deck and Q&A (IDEA.md §5, §7).

The LLM only structures and words what it is given: figures and URLs come from the
research input and are checked after the call. Every output is validated against
`app/schemas/`; an invalid answer is retried once, then raises `LLMOutputError`.
Nothing is returned (or written) until the whole output validated.
"""

from __future__ import annotations

import json
import re
from collections.abc import Callable, Iterable
from pathlib import Path

from pydantic import BaseModel, ValidationError

from app.config import settings
from app.schemas import (
    Architecture,
    BacklogItem,
    Mode,
    Pitch,
    QAEntry,
    ResearchItem,
    Spec,
)

PROMPTS_DIR = Path(__file__).parent / "prompts"
FIXTURES_DIR = Path(__file__).resolve().parent.parent / "fixtures" / "llm"

NO_DATA = "no tengo ese dato"
MIN_QUESTIONS, MAX_QUESTIONS = 3, 5
MIRO_KINDS = {"screen", "data_model", "integration", "connector"}
CLIENT_JARGON = re.compile(
    r"\b(api|backend|frontend|stack|endpoint|sql|json|microservicios?|framework|base de datos)\b",
    re.IGNORECASE,
)
NUMBER = re.compile(r"\d+(?:[.,]\d+)*")


class LLMError(Exception):
    """Base class for every error raised by this service."""


class LLMOutputError(LLMError):
    """The model output was still invalid after the single retry."""


class Passage(BaseModel):
    text: str
    source: str


# --- plumbing -------------------------------------------------------------


def _demo() -> bool:
    return bool(settings.DEMO_MODE) or not settings.ANTHROPIC_API_KEY


def _fixture(name: str):
    return json.loads((FIXTURES_DIR / f"{name}.json").read_text(encoding="utf-8"))


def _prompt(name: str) -> str:
    return "\n\n".join(
        (PROMPTS_DIR / f"{part}.md").read_text(encoding="utf-8").strip()
        for part in ("common", name)
    )


def _complete(system: str, user: str) -> str:
    """One model call. Kept tiny so tests can replace it."""
    import anthropic

    client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
    msg = client.messages.create(
        model=settings.LLM_MODEL,
        max_tokens=4096,
        system=system,
        messages=[{"role": "user", "content": user}],
    )
    return "".join(b.text for b in msg.content if getattr(b, "type", "") == "text")


def _json(text: str) -> dict:
    text = text.strip()
    fence = re.match(r"^```(?:json)?\s*(.*?)\s*```$", text, re.DOTALL)
    if fence:
        text = fence.group(1)
    data = json.loads(text)
    if not isinstance(data, dict):
        raise TypeError("expected a JSON object")
    return data


def _run[T](prompt: str, user: str, parse: Callable[[dict], T]) -> T:
    """Call the model; on invalid output retry once with the error, then raise."""
    system = _prompt(prompt)
    last: Exception | None = None
    for attempt in range(2):
        message = user
        if last is not None:
            message += f"\n\nTu respuesta anterior fue inválida: {last}. Corrígela."
        try:
            return parse(_json(_complete(system, message)))
        except (
            ValueError,
            TypeError,
            KeyError,
            ValidationError,
        ) as exc:  # JSONDecodeError is a ValueError
            last = exc
    raise LLMOutputError(f"{prompt}: invalid output after retry: {last}")


def _data(label: str, payload) -> str:
    body = (
        payload if isinstance(payload, str) else json.dumps(payload, ensure_ascii=False)
    )
    return f'<data name="{label}">\n{body}\n</data>'


def _numbers(text: str) -> set:
    return {n.rstrip(".,") for n in NUMBER.findall(text)}


def _ensure_grounded(texts: Iterable[str], corpus: Iterable[str], where: str) -> None:
    """Every figure written by the model must appear in the material it was given."""
    allowed = _numbers("\n".join(corpus))
    extra = _numbers("\n".join(texts)) - allowed
    if extra:
        raise ValueError(f"{where} has figures not in the input: {sorted(extra)}")


def _ensure_sources(cited: Iterable[str], allowed: Iterable[str], where: str) -> None:
    extra = set(cited) - set(allowed)
    if extra:
        raise ValueError(f"{where} cites URLs not in the input: {sorted(extra)}")


def _research_corpus(research: list[ResearchItem]) -> list[str]:
    return [" ".join([r.competitor, r.pricing or "", *r.features]) for r in research]


# --- public API -----------------------------------------------------------


def clarify(idea: str, mode: Mode) -> list[str]:
    """3–5 questions: technical for `dev`, plain language for `client`."""
    mode = Mode(mode)
    if _demo():
        return list(_fixture(f"clarify_{mode.value}")["questions"])

    def parse(data: dict) -> list[str]:
        questions = [
            q.strip() for q in data["questions"] if isinstance(q, str) and q.strip()
        ]
        if not MIN_QUESTIONS <= len(questions) <= MAX_QUESTIONS:
            raise ValueError(
                f"need {MIN_QUESTIONS}-{MAX_QUESTIONS} questions, got {len(questions)}"
            )
        if mode is Mode.client:
            jargon = [q for q in questions if CLIENT_JARGON.search(q)]
            if jargon:
                raise ValueError(
                    f"client questions must avoid technical jargon: {jargon}"
                )
        return questions

    return _run(f"clarify_{mode.value}", _data("idea", idea), parse)


def build_spec(
    idea: str,
    mode: Mode,
    answers: dict[str, str],
    research: list[ResearchItem],
    version: int = 1,
) -> Spec:
    """Spec citing only the research URLs received and no figure absent from the input."""
    if _demo():
        return Spec(**{**_fixture("spec"), "version": version, "demo_data": True})

    urls = [r.url for r in research]
    corpus = [
        idea,
        json.dumps(answers, ensure_ascii=False),
        *_research_corpus(research),
    ]

    def parse(data: dict) -> Spec:
        spec = Spec(**data, version=version)
        _ensure_sources(spec.sources, urls, "spec")
        _ensure_grounded(
            [spec.problem, *spec.users, *spec.mvp_features, *spec.assumptions],
            corpus,
            "spec",
        )
        return spec

    user = "\n".join(
        [
            _data("idea", idea),
            _data("mode", Mode(mode).value),
            _data("answers", answers),
            _data("research", [r.model_dump(mode="json") for r in research]),
        ]
    )
    return _run("spec", user, parse)


def build_architecture(spec: Spec) -> Architecture:
    if _demo():
        return Architecture(**{**_fixture("architecture"), "demo_data": True})

    def parse(data: dict) -> Architecture:
        arch = Architecture(**data)
        bad = [i.title for i in arch.items if i.kind not in MIRO_KINDS]
        if bad:
            raise ValueError(f"items with unknown kind: {bad}")
        return arch

    return _run("architecture", _data("spec", spec.model_dump(mode="json")), parse)


def build_backlog(spec: Spec, architecture: Architecture) -> list[BacklogItem]:
    """Backlog items; `external_id` is assigned here (BL-001…), never by the model."""
    if _demo():
        return [
            BacklogItem(**{**i, "demo_data": True})
            for i in _fixture("backlog")["items"]
        ]

    def parse(data: dict) -> list[BacklogItem]:
        raw = data["items"]
        if not raw:
            raise ValueError("backlog is empty")
        return [
            BacklogItem(
                epic=i["epic"],
                title=i["title"],
                acceptance=i["acceptance"],
                external_id=f"BL-{n:03d}",
            )
            for n, i in enumerate(raw, 1)
        ]

    user = (
        _data("spec", spec.model_dump(mode="json"))
        + "\n"
        + _data("architecture", architecture.model_dump(mode="json"))
    )
    return _run("backlog", user, parse)


def build_deck(spec: Spec, research: list[ResearchItem]) -> Pitch:
    """Pitch deck; slide sources must be research URLs and figures must come from the input."""
    if _demo():
        return Pitch(**{**_fixture("deck"), "demo_data": True})

    urls = [r.url for r in research]
    corpus = [
        json.dumps(spec.model_dump(mode="json"), ensure_ascii=False),
        *_research_corpus(research),
    ]

    def parse(data: dict) -> Pitch:
        pitch = Pitch(slides=data["slides"])
        if not pitch.slides:
            raise ValueError("deck has no slides")
        for s in pitch.slides:
            _ensure_sources(s.sources, urls, f"slide '{s.title}'")
            _ensure_grounded(s.bullets, corpus, f"slide '{s.title}'")
        return pitch

    user = (
        _data("spec", spec.model_dump(mode="json"))
        + "\n"
        + _data("research", [r.model_dump(mode="json") for r in research])
    )
    return _run("deck", user, parse)


def answer(question: str, passages: list[Passage]) -> QAEntry:
    """Answer from the passages only; with none, or none that support it, say so."""
    if not passages:
        return QAEntry(question=question, answer=NO_DATA, sources=[])
    if _demo():
        return QAEntry(**{**_fixture("answer"), "question": question})

    urls = [p.source for p in passages]

    def parse(data: dict) -> QAEntry:
        entry = QAEntry(
            question=question, answer=data["answer"], sources=data.get("sources", [])
        )
        _ensure_sources(entry.sources, urls, "answer")
        if entry.answer.strip().lower().rstrip(".") == NO_DATA:
            return QAEntry(question=question, answer=NO_DATA, sources=[])
        if not entry.sources:
            raise ValueError("answer without sources")
        _ensure_grounded(
            [entry.answer], [p.text for p in passages] + [question], "answer"
        )
        return entry

    user = (
        _data("question", question)
        + "\n"
        + _data("passages", [p.model_dump() for p in passages])
    )
    return _run("answer", user, parse)
