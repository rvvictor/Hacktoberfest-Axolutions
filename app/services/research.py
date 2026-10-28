"""Research service (HACK-005): Tavily search, cached, credit-capped, fixture fallback.

Every ResearchItem carries a URL (items without one are dropped). Without a key,
on error, or past the credit cap, recorded fixtures are used and marked demo_data.
"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Iterable, Optional

import httpx

from app.schemas.content import ResearchItem

FIXTURE = Path(__file__).resolve().parent.parent / "fixtures" / "research" / "tavily_search.json"
DEMO_QUERY = "corporate expense management software pricing Mexico"
TAVILY_URL = "https://api.tavily.com/search"
MAX_CREDITS = 5  # per-run cap on live search calls; cache hits are free

SearchFn = Callable[[str], dict]


class CreditBudget:
    def __init__(self, cap: int = MAX_CREDITS):
        self.cap, self.used = cap, 0

    def take(self) -> bool:
        if self.used >= self.cap:
            return False
        self.used += 1
        return True


def _tavily(api_key: str) -> SearchFn:
    def call(query: str) -> dict:
        r = httpx.post(
            TAVILY_URL,
            headers={"Authorization": f"Bearer {api_key}"},
            json={"query": query, "max_results": 5},
            timeout=20,
        )
        r.raise_for_status()
        return r.json()

    return call


def _cache_path(data_dir: Path, query: str) -> Path:
    return data_dir / "research_cache" / (hashlib.sha256(query.encode()).hexdigest()[:16] + ".json")


def _fixture() -> dict:
    return json.loads(FIXTURE.read_text())


def _search(query: str, data_dir: Path, search: Optional[SearchFn], budget: CreditBudget) -> dict:
    """Cache -> live (if allowed) -> fixture. Returns a Tavily-shaped dict."""
    path = _cache_path(data_dir, query)
    if path.exists():
        return json.loads(path.read_text())
    if search is not None and budget.take():
        try:
            data = search(query)
            data["fetched_at"] = datetime.now(timezone.utc).isoformat()
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(data))
            return data
        except Exception:
            pass  # fall through to the recorded fixture
    return _fixture()


def _items(data: dict) -> Iterable[ResearchItem]:
    demo = bool(data.get("demo_data"))
    fetched = data.get("fetched_at")
    for r in data.get("results", []):
        url = (r.get("url") or "").strip()
        if not url:
            continue  # no URL, no figure
        yield ResearchItem(
            competitor=r.get("title") or url,
            features=[r["content"]] if r.get("content") else [],
            url=url,
            fetched_at=datetime.fromisoformat(fetched) if fetched else None,
            demo_data=demo,
        )


def research(
    spec_draft: str,
    mode: str = "biz",
    *,
    data_dir: Path | str = Path("data"),
    api_key: Optional[str] = None,
    search: Optional[SearchFn] = None,
    stack: Iterable[str] = (),
    budget: Optional[CreditBudget] = None,
) -> list[ResearchItem]:
    """Competitor research for a spec draft; `dev` mode adds docs for each stack item."""
    data_dir = Path(data_dir)
    budget = budget or CreditBudget()
    if search is None and api_key:
        search = _tavily(api_key)
    queries = [DEMO_QUERY if not spec_draft.strip() else f"{spec_draft.strip()[:200]} competitors pricing Mexico"]
    if mode == "dev":
        queries += [f"{s} current documentation" for s in stack]
    seen: set[str] = set()
    out: list[ResearchItem] = []
    for q in queries:
        for item in _items(_search(q, data_dir, search, budget)):
            if item.url not in seen:
                seen.add(item.url)
                out.append(item)
    return out
