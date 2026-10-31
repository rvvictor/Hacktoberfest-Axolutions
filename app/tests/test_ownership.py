"""Every run belongs to its user: 401 without a session, 404 for someone else's, owner-only Hunter and Ops (HACK-077)."""

import logging
import sqlite3

import pytest
from fastapi.testclient import TestClient

from app.config import settings
from app.main import app
from app.schemas import Mode
from app.services import auth, pipeline, store

OWNER = "dueña@example.com"
ALICE = "alice@example.com"
BOB = "bob@example.com"
IDEA = "una idea secreta de alice"


def _token(sub: str, email: str) -> str:
    return auth.start_session({"sub": sub, "email": email})


@pytest.fixture
def world(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "DATA_DIR", tmp_path)
    monkeypatch.setattr(settings, "AUTH_REQUIRED", True)
    monkeypatch.setattr(settings, "OWNER_EMAIL", OWNER)
    monkeypatch.setattr(settings, "RUNS_PER_USER_PER_DAY", 100)  # the fixture already gives alice a project today (HACK-078 quota)
    # a started run would call providers: ownership must be decided before that
    monkeypatch.setattr(pipeline, "start", lambda run_id: None)
    tokens = {"alice": _token("sub-a", ALICE), "bob": _token("sub-b", BOB), "owner": _token("sub-o", OWNER)}
    _, run = store.create_run(Mode.dev, IDEA, [], demo_data=True)
    with sqlite3.connect(tmp_path / "speedhack.db") as db:
        db.execute("UPDATE projects SET owner_id=? WHERE id=?", (auth.user_for(tokens["alice"])["id"], run.project_id))
    return {"run": run.run_id, "tokens": tokens, "tmp": tmp_path}


def call(who, method, path, world, **kw):
    client = TestClient(app, base_url="https://testserver")
    if who:
        client.cookies.set(auth.SESSION_COOKIE, world["tokens"][who])
    return client.request(method, path, **kw)


def run_routes(run_id):
    return [
        ("GET", f"/api/runs/{run_id}", {}),
        ("GET", f"/api/runs/{run_id}/events", {}),
        ("POST", f"/api/runs/{run_id}/answers", {"json": {"answers": ["x"]}}),
        ("POST", f"/api/runs/{run_id}/approvals/1", {"json": {"approved": True}}),
        ("POST", f"/api/runs/{run_id}/retry", {}),
        ("GET", f"/api/pitch/{run_id}", {}),
        ("POST", f"/api/pitch/{run_id}/ask", {"json": {"question": "¿qué es?"}}),
        ("POST", f"/api/pitch/{run_id}/narration/0", {}),
        ("GET", f"/api/prototypes/{run_id}", {}),
    ]


def test_every_run_route_answers_401_without_a_session(world, monkeypatch):
    def boom(*a, **k):
        raise AssertionError("a provider was called")

    monkeypatch.setattr(pipeline, "create", boom)
    monkeypatch.setattr(pipeline, "answer", boom)
    monkeypatch.setattr(pipeline, "decide", boom)
    monkeypatch.setattr(pipeline, "retry", boom)
    routes = run_routes(world["run"]) + [("POST", "/api/projects", {"json": {"mode": "dev", "idea": "x"}})]
    for method, path, kw in routes:
        r = call(None, method, path, world, **kw)
        assert r.status_code == 401, (method, path)


def test_garbage_or_expired_session_is_401(world):
    client = TestClient(app, base_url="https://testserver")
    client.cookies.set(auth.SESSION_COOKIE, "not-a-token")
    assert client.get(f"/api/runs/{world['run']}").status_code == 401


def test_owner_of_a_run_reads_it(world):
    r = call("alice", "GET", f"/api/runs/{world['run']}", world)
    assert r.status_code == 200 and r.json()["run_id"] == world["run"]
    assert call("alice", "GET", f"/api/prototypes/{world['run']}", world).status_code in (200, 404)


def test_another_user_gets_the_unknown_run_answer(world):
    unknown = "run_00000000"
    for (method, path, kw), (_, unknown_path, _) in zip(run_routes(world["run"]), run_routes(unknown), strict=True):
        theirs = call("bob", method, path, world, **kw)
        nothing = call("bob", method, unknown_path, world, **kw)
        assert theirs.status_code == 404, (method, path, theirs.status_code)
        assert nothing.status_code == 404, (method, unknown_path)
        assert theirs.text.replace(world["run"], "X") == nothing.text.replace(unknown, "X"), path


def test_creating_a_project_records_the_owner(world):
    r = call("alice", "POST", "/api/projects", world, json={"mode": "dev", "idea": "otra idea"})
    assert r.status_code == 201
    project_id = store.get_run(r.json()["run_id"]).project_id
    with sqlite3.connect(world["tmp"] / "speedhack.db") as db:
        owner = db.execute("SELECT owner_id FROM projects WHERE id=?", (project_id,)).fetchone()[0]
    assert owner == auth.user_for(world["tokens"]["alice"])["id"]
    assert call("bob", "GET", f"/api/runs/{r.json()['run_id']}", world).status_code == 404


def test_legacy_run_without_owner_is_only_for_the_site_owner(world):
    _, legacy = store.create_run(Mode.dev, "vieja", [], demo_data=True)
    assert call("alice", "GET", f"/api/runs/{legacy.run_id}", world).status_code == 404
    assert call("owner", "GET", f"/api/runs/{legacy.run_id}", world).status_code == 200


def test_refusals_are_logged_with_the_user_and_route_but_not_the_idea(world, caplog):
    caplog.set_level(logging.INFO)
    call("bob", "GET", f"/api/runs/{world['run']}", world)
    call(None, "GET", f"/api/runs/{world['run']}", world)
    text = caplog.text
    assert "/api/runs/" in text and auth.user_for(world["tokens"]["bob"])["id"] in text
    assert IDEA not in text and BOB not in text and world["tokens"]["bob"] not in text


HUNTER = [("GET", "/api/hunter/rules"), ("GET", "/api/hunter/prospects"),
          ("POST", "/api/hunter/prospects/p1/draft"), ("POST", "/api/hunter/outreach/o1/send"),
          ("PUT", "/api/hunter/outreach/o1"), ("POST", "/api/hunter/outreach/o1/approve"),
          ("POST", "/api/hunter/outreach/o1/reply"), ("GET", "/api/ops/runs")]


@pytest.mark.parametrize("who", [None, "alice"])
def test_hunter_and_ops_are_403_for_anyone_but_the_owner(world, monkeypatch, who):
    from app.services import outreach

    def boom(*a, **k):
        raise AssertionError("something was sent")

    monkeypatch.setattr(outreach, "send", boom, raising=False)
    for method, path in HUNTER:
        r = call(who, method, path, world, **({"json": {"asks_for_call": False}} if path.endswith("reply") else {}))
        assert r.status_code == 403, (who, path)


def test_the_owner_reaches_hunter_and_ops(world):
    assert call("owner", "GET", "/api/hunter/rules", world).status_code == 200
    assert call("owner", "GET", "/api/ops/runs", world).status_code == 200


def test_nobody_is_owner_when_owner_email_is_unset(world, monkeypatch):
    monkeypatch.setattr(settings, "OWNER_EMAIL", None)
    assert call("owner", "GET", "/api/hunter/rules", world).status_code == 403


def test_the_signed_n8n_callback_needs_no_session(world):
    r = call(None, "POST", "/api/hunter/outreach/o1/callback", world,
             json={"outreach_id": "o1", "status": "sent", "sent_at": "2026-01-01T00:00:00Z"})
    assert r.status_code == 401 and r.json()["detail"] == "invalid signature"


def test_the_recorded_demo_stays_anonymous_while_demo_mode_is_on(world):
    assert call(None, "GET", "/api/pitch/demo-pitch", world).status_code == 200
    assert call(None, "POST", "/api/voice/tts", world, json={"text": "hola"}).status_code != 401


def test_demo_pitch_needs_a_session_once_demo_mode_is_off(world, monkeypatch):
    monkeypatch.setattr(settings, "DEMO_MODE", False)
    assert call(None, "GET", "/api/pitch/demo-pitch", world).status_code == 401
    assert call(None, "POST", "/api/voice/tts", world, json={"text": "hola"}).status_code == 401


def test_nothing_changes_while_auth_is_not_required(world, monkeypatch):
    monkeypatch.setattr(settings, "AUTH_REQUIRED", False)
    assert call(None, "GET", f"/api/runs/{world['run']}", world).status_code == 200
    assert call(None, "GET", "/api/hunter/rules", world).status_code == 200
    assert call(None, "GET", "/api/ops/runs", world).status_code == 200
