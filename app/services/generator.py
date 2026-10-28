"""Prototype generation: a CodeGenerator protocol with Lovable and a plan B (IDEA.md §4 step 4).

Lovable has no headless API: "Build with URL" only opens a prompt the user sends
(https://docs.lovable.dev/integrations/lovable-api), so `LovableGenerator` returns the link
and `PlanBGenerator` returns a prebuilt or recorded app labeled `demo_data: true`.
"""
from __future__ import annotations

import re
from collections.abc import Sequence
from typing import Protocol, runtime_checkable
from urllib.parse import quote

from app.config import settings
from app.schemas.content import BacklogItem, Prototype, Spec

LOVABLE_BASE_URL = "https://lovable.dev/#prompt="
MAX_PROMPT_CHARS = 50_000  # Lovable discards the whole link above this
PLANB_RECORDED_URL = "/fixtures/generator/planb/index.html"

_CONTROL = re.compile(r"[\x00-\x08\x0b-\x1f\x7f]")
_SPACES = re.compile(r"[ \t]+")


@runtime_checkable
class CodeGenerator(Protocol):
    def generate(self, spec: Spec, backlog: Sequence[BacklogItem]) -> Prototype: ...


def _clean(text: str) -> str:
    return _SPACES.sub(" ", _CONTROL.sub("", text)).strip()


def build_prompt(spec: Spec, backlog: Sequence[BacklogItem]) -> str:
    """Master prompt from validated spec and backlog fields only.

    Research items, sources and any fetched web content are deliberately not used.
    """
    lines = [
        "Build a working MVP web app prototype from this spec.",
        "",
        f"Problem: {_clean(spec.problem)}",
        "Users: " + "; ".join(_clean(u) for u in spec.users),
        "",
        "MVP features:",
        *(f"- {_clean(f)}" for f in spec.mvp_features),
    ]
    if spec.assumptions:
        lines += ["", "Assumptions:", *(f"- {_clean(a)}" for a in spec.assumptions)]
    if backlog:
        lines += ["", "Backlog (build in this order):"]
        for item in backlog:
            lines.append(f"- [{_clean(item.epic)}] {_clean(item.title)}")
            lines += [f"  - Acceptance: {_clean(a)}" for a in item.acceptance]
    lines += ["", "Use mock data where no backend exists and keep the UI simple."]
    return "\n".join(lines)[:MAX_PROMPT_CHARS]


class LovableGenerator:
    def build_url(self, spec: Spec, backlog: Sequence[BacklogItem] = ()) -> str:
        prompt = build_prompt(spec, backlog)
        return LOVABLE_BASE_URL + quote(prompt, safe="")

    def generate(self, spec: Spec, backlog: Sequence[BacklogItem]) -> Prototype:
        link = self.build_url(spec, backlog)
        return Prototype(
            generator="lovable",
            url=link,
            build_url=link,
            demo_data=spec.demo_data,
        )


class PlanBGenerator:
    def generate(self, spec: Spec, backlog: Sequence[BacklogItem] = ()) -> Prototype:
        url = settings.LOVABLE_PREBUILT_URL or PLANB_RECORDED_URL
        return Prototype(generator="planb", url=url, demo_data=True)
