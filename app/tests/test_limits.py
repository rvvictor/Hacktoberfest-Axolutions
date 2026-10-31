"""Quotas and rate limits (spec 001, HACK-078): 1 project per user per UTC day, 5 for everyone, 30 requests a minute."""

import logging
import sqlite3

import pytest
from fastapi.testclient import TestClient

from app.config import settings
from app.main import app
from app.schemas import Mode
from app.services import auth, limits, pipeline, store

ALICE = "alice@example.com"
BOB = "bob@example.com"
IDEA = "una idea muy privada de alice"
BODY = {"mode": "dev", "idea": IDEA}


@pytest.fixture
def world(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "DATA_DIR", tmp_path)
    monkeypatch.setattr(settings, "AUTH_REQUIRED", True)
    monkeypatch.setattr(settings, "RUNS_PER_USER_PER_DAY", 1)
    monkeypatch.setattr(limits.env, "MAX_PROJECTS_PER_DAY", 5)
    monkeypatch.setattr(limits.env, "REQUESTS_PER_MINUTE", 30)
    started: list[str] = []
    monkeypatch.setattr(pipeline, "start", started.append)  # a started run would call providers
    limits.reset()
    tokens = {
        name: auth.start_session({"sub": f"sub-{name}", "email": f"{name}@example.com"})
        for name in ("alice", "bob", "carol", "dave", "erin", "frank")
    }
    return {"tokens": tokens, "started": started, "tmp": tmp_path}


def call(who, method, path, world, **kw):
    client = TestClient(app, base_url="https://testserver")
    if who:
        client.cookies.set(auth.SESSION_COOKIE, world["tokens"][who])
    return client.request(method, path, **kw)


def projects(world) -> int:
    with sqlite3.connect(world["tmp"] / "speedhack.db") as db:
        return db.execute("SELECT COUNT(*) FROM projects").fetchone()[0]


def test_second_project_the_same_utc_day_answers_429_in_spanish(world):
    first = call("alice", "POST", "/api/projects", world, json=BODY)
    assert first.status_code == 201
    second = call("alice", "POST", "/api/projects", world, json=BODY)
    assert second.status_code == 429
    body = second.json()
    assert "Ya creaste 1 proyecto hoy" in body["detail"]
    assert body["resets_at"] == auth.day_window()[1] and "00:00 UTC" in body["detail"]
    assert int(second.headers["Retry-After"]) > 0
    assert projects(world) == 1 and len(world["started"]) == 1  # the refused one created and started nothing


def test_another_user_is_not_affected_by_the_first_users_quota(world):
    assert call("alice", "POST", "/api/projects", world, json=BODY).status_code == 201
    assert call("bob", "POST", "/api/projects", world, json=BODY).status_code == 201


def test_the_quota_is_a_setting(world, monkeypatch):
    monkeypatch.setattr(settings, "RUNS_PER_USER_PER_DAY", 2)
    codes = [call("alice", "POST", "/api/projects", world, json=BODY).status_code for _ in range(3)]
    assert codes == [201, 201, 429]
    assert "Ya creaste 2 proyectos hoy" in call("alice", "POST", "/api/projects", world, json=BODY).json()["detail"]


def test_a_project_from_yesterday_does_not_count(world):
    _, old = store.create_run(Mode.dev, "ayer", [], demo_data=True)
    yesterday = auth.day_window()[0] - 3600
    uid = auth.user_for(world["tokens"]["alice"])["id"]
    with sqlite3.connect(world["tmp"] / "speedhack.db") as db:
        db.execute("UPDATE projects SET owner_id=?, created=? WHERE id=?", (uid, yesterday, old.project_id))
    assert call("alice", "POST", "/api/projects", world, json=BODY).status_code == 201


def test_the_sixth_project_of_the_day_for_everyone_answers_503(world):
    for who in ("alice", "bob", "carol", "dave", "erin"):
        assert call(who, "POST", "/api/projects", world, json=BODY).status_code == 201, who
    sixth = call("frank", "POST", "/api/projects", world, json=BODY)
    assert sixth.status_code == 503
    assert "límite" in sixth.json()["detail"] and sixth.json()["resets_at"] == auth.day_window()[1]
    assert projects(world) == 5 and len(world["started"]) == 5


def test_the_global_cap_is_a_setting(world, monkeypatch):
    monkeypatch.setattr(limits.env, "MAX_PROJECTS_PER_DAY", 1)
    assert call("alice", "POST", "/api/projects", world, json=BODY).status_code == 201
    assert call("bob", "POST", "/api/projects", world, json=BODY).status_code == 503


def test_runs_already_going_keep_working_when_the_global_cap_is_reached(world, monkeypatch):
    monkeypatch.setattr(limits.env, "MAX_PROJECTS_PER_DAY", 1)
    run = call("alice", "POST", "/api/projects", world, json=BODY).json()
    assert call("bob", "POST", "/api/projects", world, json=BODY).status_code == 503
    assert call("alice", "GET", f"/api/runs/{run['run_id']}", world).status_code == 200


def test_me_reports_runs_left_and_the_reset_from_the_same_count(world):
    me = call("alice", "GET", "/api/auth/me", world).json()
    assert me["runs_left_today"] == 1 and me["resets_at"] == auth.day_window()[1]
    call("alice", "POST", "/api/projects", world, json=BODY)
    assert call("alice", "GET", "/api/auth/me", world).json()["runs_left_today"] == 0
    assert call("bob", "GET", "/api/auth/me", world).json()["runs_left_today"] == 1


def test_me_reports_zero_when_the_global_cap_is_reached(world, monkeypatch):
    monkeypatch.setattr(limits.env, "MAX_PROJECTS_PER_DAY", 1)
    call("alice", "POST", "/api/projects", world, json=BODY)
    assert call("bob", "GET", "/api/auth/me", world).json()["runs_left_today"] == 0


def test_the_31st_request_in_a_minute_to_one_route_answers_429_with_retry_after(world):
    codes = [call("alice", "GET", "/api/auth/me", world).status_code for _ in range(30)]
    assert set(codes) == {200}
    over = call("alice", "GET", "/api/auth/me", world)
    assert over.status_code == 429
    assert 1 <= int(over.headers["Retry-After"]) <= 60
    assert "Demasiadas solicitudes" in over.json()["detail"]


def test_the_rate_limit_is_per_user_and_per_route(world):
    for _ in range(30):
        call("alice", "GET", "/api/auth/me", world)
    assert call("alice", "GET", "/api/auth/me", world).status_code == 429
    assert call("bob", "GET", "/api/auth/me", world).status_code == 200  # another user
    run = call("bob", "POST", "/api/projects", world, json=BODY).json()
    assert call("alice", "POST", "/api/projects", world, json=BODY).status_code == 201  # another route
    assert call("bob", "GET", f"/api/runs/{run['run_id']}", world).status_code == 200


def test_the_window_slides(world, monkeypatch):
    now = [1000.0]
    monkeypatch.setattr(limits, "clock", lambda: now[0])
    monkeypatch.setattr(limits.env, "REQUESTS_PER_MINUTE", 2)
    assert [call("alice", "GET", "/api/auth/me", world).status_code for _ in range(3)] == [200, 200, 429]
    now[0] += 61
    assert call("alice", "GET", "/api/auth/me", world).status_code == 200


def test_the_rate_limit_applies_to_run_routes_too(world, monkeypatch):
    monkeypatch.setattr(limits.env, "REQUESTS_PER_MINUTE", 2)
    run = call("alice", "POST", "/api/projects", world, json=BODY).json()["run_id"]
    codes = [call("alice", "GET", f"/api/runs/{run}", world).status_code for _ in range(3)]
    assert codes == [200, 200, 429]


def test_a_limited_call_never_reaches_a_provider(world, monkeypatch):
    def boom(*a, **k):
        raise AssertionError("a provider was called")

    call("alice", "POST", "/api/projects", world, json=BODY)
    monkeypatch.setattr(pipeline, "create", boom)
    assert call("alice", "POST", "/api/projects", world, json=BODY).status_code == 429  # create was not reached


def test_refusals_log_user_route_and_reason_but_not_the_idea_or_email(world, caplog):
    caplog.set_level(logging.INFO)
    call("alice", "POST", "/api/projects", world, json=BODY)
    call("alice", "POST", "/api/projects", world, json=BODY)
    text = caplog.text
    assert auth.user_for(world["tokens"]["alice"])["id"] in text
    assert "/api/projects" in text and "quota" in text
    assert IDEA not in text and ALICE not in text and world["tokens"]["alice"] not in text


def test_nothing_is_limited_while_accounts_are_off(world, monkeypatch):
    monkeypatch.setattr(settings, "AUTH_REQUIRED", False)
    monkeypatch.setattr(limits.env, "MAX_PROJECTS_PER_DAY", 1)
    monkeypatch.setattr(limits.env, "REQUESTS_PER_MINUTE", 1)
    codes = [call(None, "POST", "/api/projects", world, json=BODY).status_code for _ in range(3)]
    assert codes == [201, 201, 201]
    run = call(None, "POST", "/api/projects", world, json=BODY).json()["run_id"]
    assert [call(None, "GET", f"/api/runs/{run}", world).status_code for _ in range(3)] == [200] * 3

