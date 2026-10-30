"""Cost and observability aggregation over the run store (HACK-013 tables: runs, events, costs).

The store keeps one `usd` figure per step. Tokens, credits and voice minutes are derived from it with
the price table below, so they are always labeled `estimated` unless a price is confirmed.
"""
from __future__ import annotations

import json
import sqlite3
from contextlib import closing
from pathlib import Path
from typing import Any

from app.config import settings
from app.schemas import STAGES

FIXTURE = Path(__file__).resolve().parent.parent / "fixtures" / "demo" / "run.jsonl"

# Plan budget per project, in USD. Not a published figure: estimated until the plans are priced.
PLAN_BUDGET_USD = 5.0

# service -> unit and USD per unit. `estimated` stays True until the price is checked at `source_url`.
PRICES: dict[str, dict[str, Any]] = {
    "llm": {"unit": "tokens", "usd_per_unit": 6.0 / 1_000_000, "estimated": True,
            "source_url": "https://www.anthropic.com/pricing"},
    "voice": {"unit": "minutes", "usd_per_unit": 0.10, "estimated": True,
              "source_url": "https://elevenlabs.io/pricing"},
    "credits": {"unit": "credits", "usd_per_unit": 0.05, "estimated": True,
                "source_url": "https://docs.lovable.dev/introduction/plans-and-credits"},
}

# Substrings of a step name -> service; anything else is an LLM call.
_SERVICE_HINTS = (("voice", "voice"), ("pitch", "voice"), ("elevenlabs", "voice"),
                  ("prototype", "credits"), ("lovable", "credits"), ("generator", "credits"))

# Illustrative costs for the recorded demo run (demo_data: true), not measured.
_DEMO_COSTS = {"clarify": 0.04, "research": 0.31, "spec": 0.22, "architecture": 0.18,
               "backlog": 0.12, "prototype": 0.60, "quality": 0.05, "pitch": 0.40}


def service_for(step: str) -> str:
    name = step.lower()
    return next((service for hint, service in _SERVICE_HINTS if hint in name), "llm")


def step_cost(step: str, usd: float) -> dict[str, Any]:
    price = PRICES[service_for(step)]
    return {
        "step": step,
        "usd": round(usd, 6),
        "unit": price["unit"],
        "units": round(usd / price["usd_per_unit"], 2) if price["usd_per_unit"] else 0.0,
        "estimated": price["estimated"],
        "source_url": price["source_url"],
    }


def _stages(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Status and duration per stage from stage_started / stage_done / error events."""
    out = []
    for number, name in STAGES.items():
        mine = [e for e in events if e["stage"] == number]
        start = next((e["ts"] for e in mine if e["type"] == "stage_started"), None)
        end = next((e["ts"] for e in mine if e["type"] == "stage_done"), None)
        # A recovered error (a skipped Miro note) is a warning: the stage finished with what exists.
        errors = [e for e in mine if e["type"] == "error" and not e["payload"].get("recovered")]
        warnings = [e for e in mine if e["type"] == "error" and e["payload"].get("recovered")]
        if errors:
            status = "failed"
        elif end is not None:
            status = "done"
        elif start is not None:
            status = "running"
        else:
            status = "pending"
        out.append({
            "stage": number,
            "name": name,
            "status": status,
            "duration_s": round(end - start, 2) if start is not None and end is not None else None,
            "failures": len(errors),
            "error": str(errors[-1]["payload"].get("message", "")) if errors else None,
            "warning": str(warnings[-1]["payload"].get("message", "")) if warnings else None,
        })
    return out


def _summary(run_id: str, project_id: str, status: str, demo: bool, events: list[dict[str, Any]],
             usd_by_step: dict[str, float]) -> dict[str, Any]:
    steps = [step_cost(step, usd) for step, usd in usd_by_step.items()]
    total = round(sum(s["usd"] for s in steps), 6)
    stages = _stages(events)
    return {
        "run_id": run_id,
        "project_id": project_id,
        "status": status,
        "demo_data": demo,
        "duration_s": round(max((e["ts"] for e in events), default=0.0), 2),
        "stages": stages,
        "failures": sum(s["failures"] for s in stages),
        "steps": steps,
        "total_usd": total,
        "budget_usd": PLAN_BUDGET_USD,
        "budget_used": round(total / PLAN_BUDGET_USD, 4),
        "budget_estimated": True,
    }


def _demo_run() -> dict[str, Any] | None:
    if not FIXTURE.exists():
        return None
    events = [json.loads(line) for line in FIXTURE.read_text().splitlines() if line.strip()]
    if not events:
        return None
    done = {e["stage"] for e in events if e["type"] == "stage_done"}
    status = "done" if len(done) == len(STAGES) else "running"
    return _summary(events[0]["run_id"], "prj_demo", status, True, events, _DEMO_COSTS)


def list_runs() -> list[dict[str, Any]]:
    """Real runs from the store, newest first; the recorded demo run when there are none."""
    db = settings.DATA_DIR / "speedhack.db"
    runs: list[dict[str, Any]] = []
    if db.exists():
        with closing(sqlite3.connect(db, timeout=10)) as conn:
            conn.row_factory = sqlite3.Row
            try:
                rows = conn.execute("SELECT * FROM runs ORDER BY created DESC").fetchall()
                for row in rows:
                    events = [
                        json.loads(r["event"])
                        for r in conn.execute("SELECT event FROM events WHERE run_id=? ORDER BY seq", (row["run_id"],))
                    ]
                    costs = {r["step"]: r["usd"]
                             for r in conn.execute("SELECT step, usd FROM costs WHERE run_id=?", (row["run_id"],))}
                    runs.append(_summary(row["run_id"], row["project_id"], row["status"],
                                         bool(row["demo_data"]), events, costs))
            except sqlite3.OperationalError:
                runs = []  # tables not created yet: no run has started
    if not runs and settings.DEMO_MODE and (demo := _demo_run()):
        runs = [demo]
    return runs
