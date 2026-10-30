"""A judge's general question about the project is answered from its plan; unrelated ones still are not."""

from app.config import settings
from app.schemas import QAEntry
from app.services import llm, pitch
from app.tests.test_pipeline import _approve, _create, client  # noqa: F401  (client is a fixture)

GENERAL = "¿De qué trata el proyecto?"
UNRELATED = "¿Quién ganó el mundial de 1986?"


def _finished_run(client):  # noqa: F811  (pytest fixture imported above)
    run_id = _create(client)
    client.post(f"/api/runs/{run_id}/answers", json={"answers": ["a", "b", "c"]})
    for n in (1, 2, 3):
        _approve(client, run_id, n)
    return run_id


def _ask(client, run_id, question):  # noqa: F811
    return client.post(f"/api/pitch/{run_id}/ask", json={"question": question}).json()


def test_demo_general_question_quotes_the_plan(client):  # noqa: F811
    run_id = _finished_run(client)
    answer = _ask(client, run_id, GENERAL)
    assert "no tengo ese dato" not in answer["answer"] and "Problema:" in answer["answer"]
    assert answer["sources"] and all(s.startswith("spec:") for s in answer["sources"])


def test_demo_matched_question_is_unchanged(client):  # noqa: F811
    run_id = _finished_run(client)
    answer = _ask(client, run_id, "¿Cómo funcionan las alertas?")
    assert "Alertas" in answer["answer"] and len(answer["sources"]) == 1


def test_demo_unrelated_question_still_has_no_data(client):  # noqa: F811
    run_id = _finished_run(client)
    answer = _ask(client, run_id, UNRELATED)
    assert answer["answer"].endswith("no tengo ese dato") and answer["sources"] == []


def test_live_general_question_gives_the_model_only_the_plan(monkeypatch):
    notes = [
        {"run_id": "run_live0001", "kind": "spec_note", "source": "spec:v1", "text": "Problema: los reembolsos tardan semanas."},
        {"run_id": "run_live0001", "kind": "spec_note", "source": "spec:v1", "text": "Usuarios: Finanzas; Empleados"},
    ]
    monkeypatch.setattr(settings, "DEMO_MODE", False)
    monkeypatch.setattr(llm, "_demo", lambda: False)
    monkeypatch.setattr(pitch, "recall", lambda run_id, query, k=5: notes if query == pitch.PLAN_QUERY else [])
    seen = {}

    def fake_answer(question, passages):
        seen["passages"] = passages
        return QAEntry(question=question, answer="Reduce el tiempo de reembolso.", sources=[passages[0].source])

    monkeypatch.setattr(llm, "answer", fake_answer)
    answer = pitch.ask("run_live0001", GENERAL)
    assert [p.text for p in seen["passages"]] == [n["text"] for n in notes]
    assert answer.answer.endswith("Reduce el tiempo de reembolso.") and answer.sources == ["spec:v1"]
    assert pitch.ask("run_live0001", UNRELATED).answer.endswith("no tengo ese dato")
