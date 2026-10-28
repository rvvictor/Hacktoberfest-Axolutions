"""Research service (HACK-005): Tavily search, cached, credit-capped, fixture fallback.

Every ResearchItem carries a URL (items without one are dropped). Without a key,
on error, or past the credit cap, recorded fixtures are used and marked demo_data.
"""
from __future__ import annotations

import hashlib
import json
import re
import sys
from collections.abc import Callable, Iterable
from datetime import UTC, datetime
from pathlib import Path

import httpx

from app.schemas.content import ResearchItem

# A live search or scrape that fails falls back to cache or fixture; anything else is a bug and raises.
_SERVICE_ERRORS = (httpx.HTTPError, OSError, ValueError, RuntimeError)

FIXDIR = Path(__file__).resolve().parent.parent / "fixtures" / "research"
FIXTURE = FIXDIR / "tavily_search.json"  # simulated, demo_data: true
RECORDED = FIXDIR / "recorded_tavily.json"  # real, written only by `record` with keys
STACK_FIXTURE = FIXDIR / "stack_docs.json"  # simulated, demo_data: true
FIRECRAWL_URL = "https://api.firecrawl.dev/v1/scrape"
MAX_SCRAPES = 3  # per-run cap on live Firecrawl calls; top competitor URLs only
# A price string is only ever copied verbatim from scraped page text.
PRICE_RE = re.compile(
    r"(?:US\$|MX\$|\$|USD|MXN)\s?\d[\d,]*(?:\.\d+)?(?:\s?(?:MXN|USD))?"
    r"(?:\s?(?:/|por|per)\s?(?:mo(?:nth)?|mes|user|usuario|year|año)\b)?",
    re.IGNORECASE,
)
DEMO_QUERY = "corporate expense management software pricing Mexico"
TAVILY_URL = "https://api.tavily.com/search"
MAX_CREDITS = 5  # per-run cap on live search calls; cache hits are free

SearchFn = Callable[[str], dict]
ScrapeFn = Callable[[str], str]  # url -> page markdown


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
    return json.loads((RECORDED if RECORDED.exists() else FIXTURE).read_text())


def _stack_fixture(stack_item: str) -> dict:
    """Own fallback for a dev-mode stack query: never the competitor fixture."""
    fx = json.loads(STACK_FIXTURE.read_text())
    entry = fx["stacks"].get(stack_item.strip().lower())
    if entry is None:
        slug = re.sub(r"[^a-z0-9]+", "-", stack_item.lower()).strip("-")
        entry = {k: v.format(name=stack_item, slug=slug) for k, v in fx["default"].items()}
    return {"demo_data": True, "results": [entry]}


def _firecrawl(api_key: str) -> ScrapeFn:
    def call(url: str) -> str:
        r = httpx.post(
            FIRECRAWL_URL,
            headers={"Authorization": f"Bearer {api_key}"},
            json={"url": url, "formats": ["markdown"]},
            timeout=40,
        )
        r.raise_for_status()
        return parse_firecrawl(r.json())

    return call


def parse_firecrawl(payload: dict) -> str:
    """Markdown from a Firecrawl /v1/scrape response ('' if it failed)."""
    if not payload.get("success", True):
        return ""
    return (payload.get("data") or {}).get("markdown") or ""


def extract_pricing(text: str) -> str | None:
    """First price string found verbatim in page text, else None. Never computed."""
    m = PRICE_RE.search(text or "")
    return m.group(0).strip() if m else None


def _url_cache_path(data_dir: Path, url: str) -> Path:
    return data_dir / "research_cache" / ("url_" + hashlib.sha256(url.encode()).hexdigest()[:16] + ".json")


def _scrape(url: str, data_dir: Path, scrape: ScrapeFn | None, budget: CreditBudget) -> dict | None:
    """Per-URL cache -> live Firecrawl (if allowed). None if neither."""
    path = _url_cache_path(data_dir, url)
    if path.exists():
        return json.loads(path.read_text())
    if scrape is not None and budget.take():
        try:
            page = {"url": url, "markdown": scrape(url), "fetched_at": datetime.now(UTC).isoformat()}
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(page))
            return page
        except _SERVICE_ERRORS:
            return None
    return None


def _search(query: str, data_dir: Path, search: SearchFn | None, budget: CreditBudget,
            fallback: Callable[[], dict] | None = None) -> dict:
    """Cache -> live (if allowed) -> fallback fixture. Returns a Tavily-shaped dict."""
    path = _cache_path(data_dir, query)
    if path.exists():
        return json.loads(path.read_text())
    if search is not None and budget.take():
        try:
            data = search(query)
            data["fetched_at"] = datetime.now(UTC).isoformat()
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(data))
            return data
        except _SERVICE_ERRORS:
            pass  # fall through to the recorded fixture
    return (fallback or _fixture)()


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
    api_key: str | None = None,
    firecrawl_key: str | None = None,
    search: SearchFn | None = None,
    scrape: ScrapeFn | None = None,
    stack: Iterable[str] = (),
    budget: CreditBudget | None = None,
    scrape_budget: CreditBudget | None = None,
) -> list[ResearchItem]:
    """Competitor research for a spec draft; `dev` mode adds docs for each stack item.

    Top competitor URLs are scraped (Firecrawl) and `pricing` is filled only from
    a price string found verbatim in that page; otherwise it stays None.
    """
    data_dir = Path(data_dir)
    budget = budget or CreditBudget()
    scrape_budget = scrape_budget or CreditBudget(MAX_SCRAPES)
    if search is None and api_key:
        search = _tavily(api_key)
    if scrape is None and firecrawl_key:
        scrape = _firecrawl(firecrawl_key)
    q = DEMO_QUERY if not spec_draft.strip() else f"{spec_draft.strip()[:200]} competitors pricing Mexico"
    seen: set[str] = set()
    out: list[ResearchItem] = []
    for n, item in enumerate(_items(_search(q, data_dir, search, budget))):
        if item.url in seen:
            continue
        seen.add(item.url)
        if n < MAX_SCRAPES:  # top competitor URLs only
            page = _scrape(item.url, data_dir, scrape, scrape_budget)
            if page and page.get("markdown"):
                item.pricing = extract_pricing(page["markdown"])
        out.append(item)
    if mode == "dev":
        for st in stack:
            sq = f"{st} current documentation"
            for item in _items(_search(sq, data_dir, search, budget, lambda st=st: _stack_fixture(st))):
                if item.url not in seen:
                    seen.add(item.url)
                    out.append(item)
    return out


def record(query: str = DEMO_QUERY, out_dir: Path = FIXDIR) -> None:
    """Record REAL Tavily + Firecrawl results into fixtures. Needs both keys; fakes nothing."""
    from app.config import settings

    if not (settings.TAVILY_API_KEY and settings.FIRECRAWL_API_KEY):
        sys.exit("record needs TAVILY_API_KEY and FIRECRAWL_API_KEY in .env; nothing written")
    data = _tavily(settings.TAVILY_API_KEY)(query)
    data.update(demo_data=False, query=query, fetched_at=datetime.now(UTC).isoformat())
    scrape = _firecrawl(settings.FIRECRAWL_API_KEY)
    pages = {}
    for r in data.get("results", [])[:MAX_SCRAPES]:
        if r.get("url"):
            pages[r["url"]] = scrape(r["url"])
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "recorded_tavily.json").write_text(json.dumps(data, indent=2, ensure_ascii=False))
    (out_dir / "recorded_firecrawl.json").write_text(
        json.dumps({"demo_data": False, "pages": pages}, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    if "--record" in sys.argv:
        record()
    else:
        sys.exit("usage: python -m app.services.research --record")
