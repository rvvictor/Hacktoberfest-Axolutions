"""Full judge path on one run: deck at stage 9 and Q&A answers cited from that run's memory."""

from app.services import store
from app.tests.test_pipeline import _approve, _create, _events, client  # noqa: F401  (client is a fixture)


def test_finished_run_has_deck_and_cited_answers(client):  # noqa: F811  (pytest fixture imported above)
    run_id = _create(client)
    client.post(f"/api/runs/{run_id}/answers", json={"answers": ["a", "b", "c"]})
    for n in (1, 2, 3):
        _approve(client, run_id, n)
    deck = client.get(f"/api/pitch/{run_id}").json()
    assert deck["slides"] and deck["demo_data"] is True
    pitch_ready = [e for e in _events(client, run_id) if e["type"] == "pitch_ready"]
    assert pitch_ready and pitch_ready[0]["payload"]["slides"]
    spec = store.get_spec(run_id)
    answer = client.post(f"/api/pitch/{run_id}/ask", json={"question": spec["problem"]}).json()
    assert answer["sources"] and "no tengo ese dato" not in answer["answer"]


def test_judge_asks_about_competitors_and_gets_research_sources(client):  # noqa: F811  (pytest fixture imported above)
    run_id = _create(client)
    client.post(f"/api/runs/{run_id}/answers", json={"answers": ["a", "b", "c"]})
    for n in (1, 2, 3):
        _approve(client, run_id, n)
    research_urls = {e["payload"]["url"] for e in _events(client, run_id) if e["type"] == "research_item"}
    for question in ("¿Quiénes son los competidores?", "¿Cuánto cuesta la competencia?"):
        answer = client.post(f"/api/pitch/{run_id}/ask", json={"question": question}).json()
        assert answer["sources"] and set(answer["sources"]) <= research_urls
        assert "no tengo ese dato" not in answer["answer"]
