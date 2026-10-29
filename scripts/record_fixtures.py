"""Record REAL research and LLM fixtures for the IDEA.md §3 case (HACK-025).

Run from the checkout whose `.env` holds the keys; fixtures are written next to this script:
    uv run python path/to/scripts/record_fixtures.py [--answer-only]

Research: one Tavily search + Firecrawl scrapes (`research.record`). LLM: each `app/services/llm.py`
function is called once with the real key; only validated output is saved, with `demo_data: false`.
Nothing is faked: without keys, or in DEMO_MODE, it exits before writing.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app.config import settings
from app.schemas import Mode
from app.services import llm, research

# IDEA.md §3: the developer case, and the client case (fictional barbershop, app/fixtures/client/journey.json).
DEV_IDEA = "SaaS de control de gastos corporativos con React, Supabase y alertas automatizadas"
CLIENT_IDEA = "Que mis clientes vean los precios y aparten su cita sin llamarme."
# The judge-path E2E answer (e2e/judge_path.py), given to every clarifying question.
ANSWER = "Sí: varias empresas, roles de aprobador y alertas por correo."
# The pitch Q&A fixture must cite research, so the question is one the research answers.
QUESTION = "¿Qué soluciones de gestión de gastos existen y qué ofrecen?"


def _write(name: str, data: dict) -> None:
    path = llm.FIXTURES_DIR / f"{name}.json"
    path.write_text(json.dumps({**data, "demo_data": False}, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"wrote {path.relative_to(ROOT)}", flush=True)


def _qa(items: list) -> dict:
    passages = [llm.Passage(text=" ".join(i.features), source=i.url) for i in items if i.features]
    qa = llm.answer(QUESTION, passages)
    if not qa.sources:
        sys.exit(f"the answer cites no research ({qa.answer!r}); answer fixture not written")
    return qa.model_dump(mode="json", exclude={"question", "demo_data"})


def main(argv: list[str]) -> int:
    if settings.DEMO_MODE or llm._demo():
        sys.exit("DEMO_MODE is on or the LLM key is missing; nothing written")
    if "--answer-only" not in argv:
        research.record()
    recorded = json.loads(research.RECORDED.read_text(encoding="utf-8"))
    items = list(research._items(recorded))
    if not items:
        sys.exit("research recording has no item with a URL; LLM fixtures not written")
    print(f"research: {len(items)} items with URL", flush=True)
    if "--answer-only" in argv:
        _write("answer", _qa(items))
        return 0

    questions = {m: llm.clarify(idea, m) for m, idea in ((Mode.dev, DEV_IDEA), (Mode.client, CLIENT_IDEA))}
    answers = {q: ANSWER for q in questions[Mode.dev]}
    spec = llm.build_spec(DEV_IDEA, Mode.dev, answers, items)
    arch = llm.build_architecture(spec)
    backlog = llm.build_backlog(spec, arch)
    deck = llm.build_deck(spec, items)
    qa = _qa(items)

    for m, qs in questions.items():
        _write(f"clarify_{m.value}", {"questions": qs})
    _write("spec", spec.model_dump(mode="json", exclude={"version", "demo_data"}))
    _write("architecture", arch.model_dump(mode="json", exclude={"demo_data"}))
    _write("backlog", {"items": [i.model_dump(mode="json", exclude={"demo_data"}) for i in backlog]})
    _write("deck", deck.model_dump(mode="json", exclude={"demo_data"}))
    _write("answer", qa)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
