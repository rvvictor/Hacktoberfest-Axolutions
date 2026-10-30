"""HACK-063: research queries come from the idea; junk pages and lone prices never reach the plan.

No network: Tavily responses are shaped like the junk of run_242dc4bf (see the task) and reconstructed
by hand. The titles come from the task; the paths are illustrative, not the recording.
"""
import json

import pytest

from app.schemas import Mode
from app.services import llm, stages
from app.services import research as R

PUMPS = "catálogo de bombas de agua y motores"
JUNK = {
    "results": [
        {"title": "How to Start a Clothing Business | Indeed.com",
         "url": "https://www.indeed.com/career-advice/starting-a-business/how-to-start-a-clothing-business",
         "content": "A guide to starting a clothing business."},
        {"title": "Marketing for small businesses (SMEs) | Indeed.com",
         "url": "https://www.indeed.com/career-advice/career-development/sme-marketing",
         "content": "Marketing tips."},
        {"title": "Kraken (KRKN) stock price today", "url": "https://www.kraken.com/prices/krkn",
         "content": "Price $1.02"},
        {"title": "Pump Catalog Co. competitors | CB Insights", "url": "https://www.cbinsights.com/company/pumpco",
         "content": "Profile."},
    ]
}
REAL = {"title": "Grundfos | Catálogo de bombas", "url": "https://www.grundfos.com/mx/products",
        "content": "Bombas de agua para uso doméstico e industrial."}


def _live(results):
    return lambda q: {"results": results}


def test_junk_results_of_the_real_run_are_dropped(tmp_path):
    items = R.research(PUMPS, data_dir=tmp_path, search=_live([*JUNK["results"][:3], REAL]))
    assert [i.url for i in items] == [REAL["url"]]


def test_lone_dollar_is_not_a_price(tmp_path):
    items = R.research(PUMPS, data_dir=tmp_path, search=_live([JUNK["results"][3]]),
                       scrape=lambda u: "# CB Insights\n\nGet started for $1 today.\nPricing: $1")
    assert items[0].pricing is None


@pytest.mark.parametrize("md, price", [
    ("# Acme\n\nStarter: $99 USD per month", "$99 USD per month"),
    ("| Plan | Precio |\n| Pro | $29/mes |", "$29/mes"),
    ("## Business\n\n$199 per month", "$199 per month"),
    ("Prices from $1 for new users", None),
    ("Desde $50 en tu primera compra", None),
])
def test_price_needs_a_plan_name_next_to_it(md, price):
    assert R.extract_plan_pricing(md) == price


def test_queries_drive_the_search_and_results_merge(tmp_path):
    calls = []

    def search(q):
        calls.append(q)
        return {"results": [{"title": f"Vendor {len(calls)}", "url": f"https://v{len(calls)}.mx/productos",
                             "content": "c"}]}

    items = R.research(PUMPS, data_dir=tmp_path, search=search,
                       queries=["distribuidores de bombas de agua México", "catálogo bombas motores precio"])
    assert calls == ["distribuidores de bombas de agua México", "catálogo bombas motores precio"]
    assert len(items) == 2


def test_nothing_relevant_returns_empty_not_padding(tmp_path):
    assert R.research(PUMPS, data_dir=tmp_path, search=_live(JUNK["results"][:3])) == []


def test_expense_saas_idea_keeps_competitors(tmp_path):
    res = [{"title": "Clara | Tarjetas y control de gastos", "url": "https://www.clara.com/mx", "content": "Gastos."},
           {"title": "Cómo controlar los gastos de tu empresa - Guía", "url": "https://blog.example.test/gastos",
            "content": "guía"}]
    items = R.research("dashboard de gastos", data_dir=tmp_path, search=_live(res))
    assert [i.url for i in items] == ["https://www.clara.com/mx"]


# --- query builder (llm) -----------------------------------------------------------------------


@pytest.fixture
def live(monkeypatch):
    monkeypatch.setattr(llm, "_demo", lambda: False)


def _answer(monkeypatch, payload):
    seen = []
    monkeypatch.setattr(llm, "_complete", lambda system, user, **kw: seen.append(user) or json.dumps(payload))
    return seen


def test_research_queries_from_idea_and_answers(live, monkeypatch):
    seen = _answer(monkeypatch, {"queries": ["catálogo de bombas de agua", "distribuidores de motores eléctricos"]})
    qs = llm.research_queries(PUMPS, Mode.client, {"¿Para quién?": "ferreterías de Jalisco"})
    assert qs == ["catálogo de bombas de agua", "distribuidores de motores eléctricos"]
    assert PUMPS in seen[0] and "ferreterías" in seen[0]


@pytest.mark.parametrize("bad", [
    {"queries": []}, {"queries": ["a", "b", "c", "d"]}, {"queries": ["https://x.com precios"]},
    {"queries": ["bombas $1"]}, {"queries": [""]},
])
def test_research_queries_reject_results_figures_and_urls(live, monkeypatch, bad):
    _answer(monkeypatch, bad)
    with pytest.raises(llm.LLMOutputError):
        llm.research_queries(PUMPS, Mode.client, {})


def test_research_queries_without_key_is_none(monkeypatch):
    monkeypatch.setattr(llm, "_demo", lambda: True)
    assert llm.research_queries(PUMPS, Mode.client, {}) is None


def test_stage_falls_back_to_the_idea_when_the_llm_fails(monkeypatch):
    def boom(*a, **k):
        raise llm.LLMOutputError("bad")

    monkeypatch.setattr(llm, "research_queries", boom)
    assert stages._research_queries("idea de prueba", Mode.client, {"q": "x"}) == ["idea de prueba"]
