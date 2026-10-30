"""The pitch is a real deck: a cover, the recorded deck in demo, sources only from the run's research (HACK-066)."""

import json

import pytest
from fastapi.testclient import TestClient

from app.config import settings
from app.main import app
from app.schemas import Pitch, ResearchItem, Spec
from app.services import llm, pitch
from app.tests.test_pipeline import _approve, _create, _events, client  # noqa: F401  (client is a fixture)

RECORDED = [s["title"] for s in json.loads((llm.FIXTURES_DIR / "deck.json").read_text(encoding="utf-8"))["slides"]]


def _finished_run(client):  # noqa: F811  (pytest fixture imported above)
    run_id = _create(client)
    client.post(f"/api/runs/{run_id}/answers", json={"answers": ["a", "b", "c"]})
    for n in (1, 2, 3):
        _approve(client, run_id, n)
    return run_id


def _check_layout(slides):
    assert slides[0]["bullets"] and len(slides[0]["bullets"]) == 1  # the cover: a name and one line
    assert all(len(s["bullets"]) <= 4 for s in slides)


def test_demo_run_shows_the_recorded_deck_after_a_cover(client):  # noqa: F811
    run_id = _finished_run(client)
    research = {e["payload"]["url"] for e in _events(client, run_id) if e["type"] == "research_item"}
    deck = client.get(f"/api/pitch/{run_id}").json()
    slides = deck["slides"]
    assert deck["demo_data"] is True
    assert slides[0]["title"] == "SaaS de gastos"
    assert [s["title"] for s in slides[1:]] == RECORDED
    _check_layout(slides)
    cited = {src for s in slides[1:] for src in s["sources"]}
    assert cited and cited <= research


def test_demo_pitch_sample_shows_the_recorded_deck_with_its_own_evidence(monkeypatch):
    monkeypatch.setattr(settings, "DEMO_MODE", True)
    slides = TestClient(app).get("/api/pitch/demo-pitch").json()["slides"]
    assert slides[0]["sources"] == ["demo:spec"]
    assert [s["title"] for s in slides[1:]] == RECORDED
    _check_layout(slides)
    research = {p["source"] for p in pitch.DEMO_PASSAGES if p["kind"] == "research"}
    assert {src for s in slides[1:] for src in s["sources"]} <= research


def test_live_deck_drops_sources_outside_the_research_and_caps_bullets(monkeypatch):
    spec = Spec(version=1, problem="Los pedidos de bombas se cotizan por teléfono. Tarda días.", users=[], mvp_features=[])
    found = ResearchItem(competitor="Rival", url="https://rival.test/pricing")
    records = [
        {"run_id": "run_live0001", "kind": "spec", "text": spec.model_dump_json(), "source": "spec:1"},
        {"run_id": "run_live0001", "kind": "research", "text": found.model_dump_json(), "source": found.url},
    ]
    monkeypatch.setattr(settings, "DEMO_MODE", False)
    monkeypatch.setattr(pitch, "recall", lambda *a, **k: records)
    monkeypatch.setattr(pitch, "_idea", lambda run_id: "catálogo de bombas de agua y motores, con cotización en línea")
    monkeypatch.setattr(llm, "_demo", lambda: False)
    monkeypatch.setattr(llm, "build_deck", lambda s, r: Pitch(slides=[
        {"title": "Mercado", "bullets": ["a", "b", "c", "d", "e", "f"], "sources": [found.url, "https://otro.test"]},
        {"title": "Inventado", "bullets": ["$99 al mes"], "sources": ["https://otro.test"]},
        {"title": "Equipo", "bullets": ["Dos personas"], "sources": []},
    ]))

    slides = [s.model_dump() for s in pitch.deck("run_live0001").slides]

    assert slides[0] == {"title": "Catálogo de bombas de agua y motores",
                         "bullets": ["Los pedidos de bombas se cotizan por teléfono."], "sources": ["spec:1"]}
    assert [s["title"] for s in slides[1:]] == ["Mercado", "Equipo"]
    assert slides[1]["sources"] == [found.url] and slides[1]["bullets"] == ["a", "b", "c", "d"]


@pytest.mark.parametrize("idea,name", [
    ("SaaS de control de gastos corporativos con React, Supabase y alertas automatizadas",
     "SaaS de control de gastos corporativos"),
    ("negocio de catálogo de productos de bombas de agua y motores", "Negocio de catálogo de productos de bombas de agua y motores"),
    ("x" * 120, "X" + "x" * 58 + "…"),
])
def test_cover_name_is_a_short_title_from_the_idea(idea, name):
    assert pitch.cover_name(idea) == name
