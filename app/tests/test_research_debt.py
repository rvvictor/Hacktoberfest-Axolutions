"""Debt from the HACK-063 security review: input caps and no idea text in the logs (HACK-071)."""
import logging

import pytest
from fastapi.testclient import TestClient

from app.config import settings
from app.main import app
from app.routers import runs
from app.schemas import Mode
from app.services import llm, stages

IDEA = "Catálogo de bombas de agua y motores para un negocio familiar"


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "DATA_DIR", tmp_path)
    monkeypatch.setattr(settings, "DEMO_MODE", True)
    monkeypatch.setenv("DEMO_SPEED", "0")
    return TestClient(app)


def test_an_idea_over_the_cap_is_a_422_in_spanish(client):
    r = client.post("/api/projects", json={"mode": "dev", "idea": "x" * (runs.IDEA_MAX + 1)})
    assert r.status_code == 422
    assert "La idea es demasiado larga" in r.text


def test_an_idea_at_the_cap_is_accepted(client):
    r = client.post("/api/projects", json={"mode": "dev", "idea": "x" * runs.IDEA_MAX})
    assert r.status_code == 201


def test_an_answer_over_the_cap_is_a_422_in_spanish(client):
    run_id = client.post("/api/projects", json={"mode": "dev", "idea": IDEA}).json()["run_id"]
    r = client.post(f"/api/runs/{run_id}/answers", json={"answers": ["ok", "y" * (runs.ANSWER_MAX + 1)]})
    assert r.status_code == 422
    assert "Una respuesta es demasiado larga" in r.text


def test_failed_research_queries_are_logged_by_type_only(caplog, monkeypatch):
    secret_answer = "mi proveedor es Bombas Secretas SA"

    def bad_queries(idea, mode, answers):
        raise llm.LLMOutputError(f"research_queries: invalid output after retry: {idea} {secret_answer}")

    monkeypatch.setattr(llm, "research_queries", bad_queries)
    with caplog.at_level(logging.DEBUG, logger=stages.log.name):
        queries = stages._research_queries(IDEA, Mode.client, {"¿Quién te surte?": secret_answer})

    assert queries == [IDEA]
    text = "\n".join(r.getMessage() + (r.exc_text or "") for r in caplog.records)
    assert "LLMOutputError" in text
    assert IDEA not in text and secret_answer not in text and "Bombas" not in text
    assert all(r.exc_info is None for r in caplog.records)  # a traceback would carry the message
