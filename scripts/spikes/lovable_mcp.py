"""HACK-068 spike helper: what SpeedHack would send to Lovable, and how a server could authenticate.

    uv run python scripts/spikes/lovable_mcp.py RUN_ID      # prints the build prompt for that run
    uv run python scripts/spikes/lovable_mcp.py --discovery # prints Lovable's OAuth discovery (public, no credits)

The spike itself called the Lovable MCP server (https://mcp.lovable.dev) from a Claude Code session already
authorized by Dylan (OAuth in the browser); results are in docs/specs/002-real-product/spike-lovable.md.
No token is read, printed or stored here.
"""

from __future__ import annotations

import json
import sqlite3
import sys
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from app.config import settings
from app.schemas.content import BacklogItem, Spec
from app.services import generator

DISCOVERY = (
    "https://mcp.lovable.dev/.well-known/oauth-protected-resource",
    "https://lovable.dev/.well-known/oauth-authorization-server",
)


def build_prompt(run_id: str) -> str:
    """The prompt `generator.build_prompt` makes from the run's latest spec and backlog."""
    db = sqlite3.connect(Path(settings.DATA_DIR) / "speedhack.db")
    spec, backlog = None, []
    for (raw,) in db.execute("select event from events where run_id=? order by seq", (run_id,)):
        event = json.loads(raw)
        if event["type"] == "spec_ready":
            spec = Spec.model_validate(event["payload"])
        elif event["type"] == "linear_issue":
            backlog.append(BacklogItem.model_validate({k: v for k, v in event["payload"].items() if k in BacklogItem.model_fields}))
    if spec is None:
        sys.exit(f"{run_id}: no spec_ready event in {settings.DATA_DIR}")
    return generator.build_prompt(spec, backlog)


def discovery() -> dict:
    keep = ("resource", "authorization_servers", "scopes_supported", "issuer", "authorization_endpoint",
            "token_endpoint", "registration_endpoint", "grant_types_supported", "code_challenge_methods_supported")
    out = {}
    for url in DISCOVERY:
        data = httpx.get(url, timeout=20).json()
        out[url] = {k: data[k] for k in keep if k in data}
    return out


if __name__ == "__main__":
    if sys.argv[1:] == ["--discovery"]:
        print(json.dumps(discovery(), indent=2))
    elif len(sys.argv) == 2:
        print(build_prompt(sys.argv[1]))
    else:
        sys.exit(__doc__)
