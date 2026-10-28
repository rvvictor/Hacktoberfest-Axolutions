import json

from app.services import research as R

FX = json.loads((R.FIXDIR / "firecrawl_pricing.json").read_text())  # simulated, demo_data: true


def _fake(calls):
    def f(q):
        calls.append(q)
        return {"results": [{"title": f"Co {len(calls)}", "url": f"https://x.test/{len(calls)}", "content": "c"},
                            {"title": "nourl", "url": "", "content": "c"}]}
    return f


def test_fixture_fallback_gives_three_items_marked_demo(tmp_path):
    items = R.research("gastos corporativos", data_dir=tmp_path)
    assert len(items) >= 3 and all(i.url and i.demo_data for i in items)


def test_live_results_are_cached_and_drop_missing_url(tmp_path):
    calls = []
    a = R.research("x", data_dir=tmp_path, search=_fake(calls))
    b = R.research("x", data_dir=tmp_path, search=_fake(calls))
    assert len(calls) == 1 and [i.url for i in a] == [i.url for i in b] == ["https://x.test/1"]
    assert not a[0].demo_data and a[0].fetched_at


def test_dev_mode_adds_stack_docs(tmp_path):
    calls = []
    R.research("x", "dev", data_dir=tmp_path, search=_fake(calls), stack=["Supabase Auth"])
    assert calls[-1] == "Supabase Auth current documentation" and len(calls) == 2


def test_dev_stack_without_key_uses_own_demo_fixture(tmp_path):
    items = R.research("x", "dev", data_dir=tmp_path, stack=["Supabase Auth", "Foo DB"])
    docs = [i for i in items if "/docs/" in i.url]
    assert [i.url for i in docs] == ["https://example.invalid/docs/supabase-auth", "https://example.invalid/docs/foo-db"]
    assert all(i.demo_data for i in docs)
    assert not any("research/a" in d.url for d in docs)


def test_parse_firecrawl_response_and_failure():
    assert "Starter" in R.parse_firecrawl(FX["response"])
    assert R.parse_firecrawl(FX["failed"]) == ""


def test_pricing_extracted_verbatim_or_none():
    md = FX["response"]["data"]["markdown"]
    assert R.extract_pricing(md) == "$99 USD per month"
    assert R.extract_pricing(FX["no_price_markdown"]) is None


def test_pricing_filled_from_scrape_and_url_cache_hits(tmp_path):
    scraped = []

    def scrape(url):
        scraped.append(url)
        return R.parse_firecrawl(FX["response"])

    a = R.research("x", data_dir=tmp_path, search=_fake([]), scrape=scrape)
    assert a[0].pricing == "$99 USD per month" and scraped == ["https://x.test/1"]
    # new query text -> search cache miss, same URL -> per-URL cache hit, no new scrape
    b = R.research("y", data_dir=tmp_path, search=lambda q: {"results": [{"title": "T", "url": "https://x.test/1"}]},
                   scrape=scrape)
    assert b[0].pricing == "$99 USD per month" and scraped == ["https://x.test/1"]


def test_no_scrape_or_no_price_leaves_pricing_null(tmp_path):
    assert R.research("x", data_dir=tmp_path / "a", search=_fake([]))[0].pricing is None
    r = R.research("x", data_dir=tmp_path / "b", search=_fake([]), scrape=lambda u: FX["no_price_markdown"])
    assert r[0].pricing is None


def test_scrape_cap_and_error_tolerated(tmp_path):
    def boom(u):
        raise RuntimeError("down")
    items = R.research("x", data_dir=tmp_path, search=_fake([]), scrape=boom)
    assert items[0].pricing is None and items[0].url


def test_credit_cap_falls_back_to_fixture(tmp_path):
    calls = []
    b = R.CreditBudget(1)
    items = R.research("x", "dev", data_dir=tmp_path, search=_fake(calls), stack=["A", "B"], budget=b)
    assert len(calls) == 1 and any(i.demo_data for i in items)


def test_search_error_falls_back(tmp_path):
    def boom(q):
        raise RuntimeError("down")
    assert all(i.demo_data for i in R.research("x", data_dir=tmp_path, search=boom))
