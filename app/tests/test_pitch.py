from fastapi.testclient import TestClient

from app.main import app
from app.schemas import QAEntry
from app.services import pitch

client = TestClient(app)


def test_demo_deck_and_disclosure(monkeypatch):
    monkeypatch.setattr(pitch.settings, "DEMO_MODE", True)
    response = client.get("/api/pitch/demo-pitch")
    assert response.status_code == 200
    assert response.json()["demo_data"] is True
    assert response.json()["slides"][0]["sources"] == ["demo:spec"]
    answer = client.post(
        "/api/pitch/demo-pitch/ask", json={"question": "¿Quién ganó el mundial?"}
    ).json()
    assert answer["answer"] == "Soy una IA. no tengo ese dato"
    assert answer["sources"] == []


def test_recall_and_llm_contract(monkeypatch):
    record = {
        "run_id": "run-a",
        "text": "Las alertas llegan por correo",
        "source": "spec:1",
        "demo_data": True,
    }
    monkeypatch.setattr(pitch, "recall", lambda run, query, k=5: [record])
    calls = []

    def answer(question, passages):
        calls.append((question, passages))
        return QAEntry(
            question=question,
            answer="Las alertas llegan por correo",
            sources=["spec:1"],
        )

    monkeypatch.setattr(pitch.llm, "answer", answer)
    result = client.post(
        "/api/pitch/run-a/ask", json={"question": "¿Cómo llegan las alertas?"}
    ).json()
    assert result["sources"] == ["spec:1"]
    assert result["demo_data"] is True
    assert calls[0][1][0].text == record["text"]
    assert pitch.ask("run-b", "alertas").sources == []
    assert len(calls) == 1


def test_irrelevant_and_fabricated_sources_fail_closed(monkeypatch):
    monkeypatch.setattr(
        pitch,
        "recall",
        lambda *a, **k: [
            {"run_id": "a", "text": "Alertas por correo", "source": "spec:1"}
        ],
    )
    monkeypatch.setattr(
        pitch.llm,
        "answer",
        lambda q, p: QAEntry(question=q, answer="Inventado", sources=["inventada"]),
    )
    assert pitch.ask("a", "alertas").answer.endswith(pitch.NO_DATA)
    monkeypatch.setattr(
        pitch.llm,
        "answer",
        lambda *a: (_ for _ in ()).throw(
            AssertionError("irrelevant passage reached LLM")
        ),
    )
    assert pitch.ask("a", "ganancias mensuales").sources == []


def test_validation_and_empty_deck(monkeypatch):
    for question in ["", "   ", "x" * 2001]:
        assert (
            client.post("/api/pitch/a/ask", json={"question": question}).status_code
            == 422
        )
    monkeypatch.setattr(pitch, "recall", lambda *a, **k: [])
    assert client.get("/api/pitch/a").json()["slides"] == []


def test_unavailable_is_retryable(monkeypatch):
    def unavailable(*args, **kwargs):
        raise pitch.PitchUnavailable()

    monkeypatch.setattr(pitch, "recall", unavailable)
    assert client.get("/api/pitch/a").status_code == 503
    assert (
        client.post("/api/pitch/a/ask", json={"question": "alertas"}).status_code == 503
    )
