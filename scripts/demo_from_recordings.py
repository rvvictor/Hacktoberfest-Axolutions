"""Rebuild the demo replays from the real recordings of HACK-025 (no keys, no network).

    uv run python scripts/demo_from_recordings.py

- `app/fixtures/demo/run.jsonl`: stage-3 `research_item` events come from `recorded_tavily.json` exactly as
  `research.research` serves them, `pricing` only when `extract_pricing` finds it verbatim in the recorded page;
  the stage-4 `spec_ready` payload is `app/fixtures/llm/spec.json`; stage-5 `miro_item` events are what the
  live board (`miro.BoardRun`) emits for the recorded `architecture.json`, run against a local stand-in for the
  Miro API; stage-6 `linear_issue` events are the recorded `backlog.json`;
  the stage-7 fallback is the plan B page.
- The web local replays get the same data between their `// <recorded>` markers.
Every event and item keeps `demo_data: true`. Nothing is typed by hand.
"""

from __future__ import annotations

import asyncio
import itertools
import json
import re
import sys
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app.config import settings
from app.schemas import Architecture
from app.services import generator, miro, research

RUN = ROOT / "app" / "fixtures" / "demo" / "run.jsonl"
SPEC = ROOT / "app" / "fixtures" / "llm" / "spec.json"
ARCHITECTURE = ROOT / "app" / "fixtures" / "llm" / "architecture.json"
BACKLOG = ROOT / "app" / "fixtures" / "llm" / "backlog.json"
PAGES = research.FIXDIR / "recorded_firecrawl.json"
# Each web replay gets only the constants it uses (TypeScript flags unused locals).
WEB = {
    ROOT / "web" / "src" / "features" / "project" / "demo.ts": ("RESEARCH", "SPEC", "BOARD", "BACKLOG"),
    ROOT / "web" / "src" / "features" / "spec" / "demo.ts": ("RESEARCH", "SPEC"),
    ROOT / "web" / "src" / "features" / "live-board" / "demo.ts": ("BOARD", "BACKLOG"),
}

BLOCK = re.compile(r"// <recorded>\n.*?// </recorded>\n", re.DOTALL)
# Scraped page text can carry emoji; the UI uses its own icon set (design-lint), so they are dropped from the text.
EMOJI = re.compile(r"[\U0001F000-\U0001FAFF\u2600-\u27BF\uFE0F]")


def recorded_research() -> list[dict]:
    pages = json.loads(PAGES.read_text(encoding="utf-8"))["pages"]
    items = []
    for item in research._items(json.loads(research.RECORDED.read_text(encoding="utf-8"))):
        item.pricing = research.extract_pricing(pages.get(item.url) or "")
        item.features = [EMOJI.sub("", f) for f in item.features]
        items.append({**item.model_dump(mode="json"), "demo_data": True})
    return items


def recorded_spec(urls: list[str]) -> dict:
    spec = {**json.loads(SPEC.read_text(encoding="utf-8")), "version": 1, "demo_data": True}
    if not set(spec["sources"]) <= set(urls):
        sys.exit("spec.json cites a URL that is not in the research recording; nothing written")
    return spec


def recorded_board() -> list[dict]:
    """The events the live board code emits for the recorded architecture; Miro ids are local demo ids."""
    counter = itertools.count(1)
    api = httpx.MockTransport(lambda _request: httpx.Response(201, json={"id": f"demo_miro_{next(counter)}"}))
    architecture = Architecture.model_validate(json.loads(ARCHITECTURE.read_text(encoding="utf-8")))

    async def run() -> list[dict]:
        async with httpx.AsyncClient(transport=api) as client:
            board = miro.BoardRun(architecture, demo=False, client=client, sleep=_no_wait)
            return [{**item, "demo_data": True} async for item in board]

    settings.MIRO_ACCESS_TOKEN = settings.MIRO_ACCESS_TOKEN or "local-stand-in"  # never sent anywhere
    return asyncio.run(run())


async def _no_wait(_seconds: float) -> None:
    return None


def recorded_backlog() -> list[dict]:
    items = json.loads(BACKLOG.read_text(encoding="utf-8"))["items"]
    return [{**item, "linear_id": f"DEMO-{n}", "url": None, "demo_data": True} for n, item in enumerate(items, 1)]


def _replace(lines: list[dict], stage: int, etype: str, payloads: list[dict]) -> list[dict]:
    """Swap a stage's events of one type for `payloads`, spread evenly before that stage's stage_done."""
    first = next(i for i, d in enumerate(lines) if d["stage"] == stage and d["type"] == etype)
    template = lines[first]
    kept = [d for d in lines if not (d["stage"] == stage and d["type"] == etype)]
    done = next(d["ts"] for d in kept[first:] if d["stage"] == stage and d["type"] == "stage_done")
    step = (done - template["ts"]) / (len(payloads) + 1)
    fresh = [{**template, "payload": p, "ts": round(template["ts"] + step * n, 1)} for n, p in enumerate(payloads)]
    return kept[:first] + fresh + kept[first:]


def rewrite_run(data: dict[str, list[dict] | dict]) -> None:
    lines = [json.loads(line) for line in RUN.read_text(encoding="utf-8").splitlines() if line.strip()]
    out = _replace(lines, 3, "research_item", data["RESEARCH"])
    out = _replace(out, 5, "miro_item", data["BOARD"])
    out = _replace(out, 6, "linear_issue", data["BACKLOG"])
    spec = data["SPEC"]
    for d in out:
        if d["type"] == "spec_ready":
            d["payload"] = spec
        elif d["type"] == "prototype_ready":
            # Only replayed when the live stage 7 fails (HACK-051 runs it even in DEMO_MODE).
            d["payload"] = {"generator": "planb", "url": generator.PLANB_RECORDED_URL, "build_url": None,
                            "repo_url": None, "demo_data": True}
    RUN.write_text("".join(json.dumps(d, ensure_ascii=False) + "\n" for d in out), encoding="utf-8")


def rewrite_web(data: dict[str, list[dict] | dict]) -> None:
    # The web replay draws the board with its own tokens (design-lint): Miro's hex colors stay in run.jsonl only.
    data = {**data, "BOARD": [{k: v for k, v in item.items() if k != "color"} for item in data["BOARD"]]}
    for path, names in WEB.items():
        body = (
            "// <recorded>\n"
            "// Generated by scripts/demo_from_recordings.py from the HACK-025 recordings; do not edit by hand.\n"
            + "".join(f"const RECORDED_{name} = {json.dumps(data[name], ensure_ascii=False, indent=2)};\n" for name in names)
            + "// </recorded>\n"
        )
        text = path.read_text(encoding="utf-8")
        if not BLOCK.search(text):
            sys.exit(f"{path.relative_to(ROOT)} has no // <recorded> block")
        path.write_text(BLOCK.sub(lambda _m, body=body: body, text, count=1), encoding="utf-8")


def main() -> int:
    items = recorded_research()
    data = {"RESEARCH": items, "SPEC": recorded_spec([i["url"] for i in items]),
            "BOARD": recorded_board(), "BACKLOG": recorded_backlog()}
    rewrite_run(data)
    rewrite_web(data)
    print(f"demo replays rebuilt: {len(items)} research items, spec citing {len(data['SPEC']['sources'])} sources, "
          f"{len(data['BOARD'])} board items, {len(data['BACKLOG'])} issues")
    return 0


if __name__ == "__main__":
    sys.exit(main())
