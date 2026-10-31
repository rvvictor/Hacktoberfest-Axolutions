"""Sign in with Google: OIDC code flow with PKCE and state, hashed sessions, /api/auth/* (HACK-076)."""

import base64
import hashlib
import json
import logging
import sqlite3
import time
from urllib.parse import parse_qs, urlparse

import httpx
import pytest
import respx
from fastapi.testclient import TestClient

from app.config import settings
from app.main import app
from app.schemas import Mode
from app.services import auth, store

CLIENT_ID = "client-123.apps.googleusercontent.com"
EMAIL = "persona@example.com"
CODE = "4/secret-code"


def _id_token(**claims):
    body = {"iss": "https://accounts.google.com", "aud": CLIENT_ID, "sub": "google-sub-1", "email": EMAIL,
            "email_verified": True, "exp": int(time.time()) + 600, **claims}

    def part(data):
        return base64.urlsafe_b64encode(json.dumps(data).encode()).rstrip(b"=").decode()

    return f"{part({'alg': 'RS256'})}.{part(body)}.c2lnbmF0dXJl"


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "DATA_DIR", tmp_path)
    monkeypatch.setattr(settings, "GOOGLE_CLIENT_ID", CLIENT_ID)
    monkeypatch.setattr(settings, "GOOGLE_CLIENT_SECRET", "client-secret")
    return TestClient(app, base_url="https://testserver")


def _login(client):
    r = client.get("/api/auth/google/login", follow_redirects=False)
    assert r.status_code in (302, 307)
    return parse_qs(urlparse(r.headers["location"]).query)


def _callback(client, token_body, state=None, **params):
    query = _login(client)
    with respx.mock(assert_all_called=False) as router:
        route = router.post(auth.GOOGLE_TOKEN_URL).mock(return_value=httpx.Response(200, json=token_body))
        r = client.get("/api/auth/google/callback", params={"code": CODE, "state": state or query["state"][0], **params},
                       follow_redirects=False)
    return r, route, query


def test_login_redirects_to_google_with_state_and_pkce(client):
    r = client.get("/api/auth/google/login", follow_redirects=False)
    url = urlparse(r.headers["location"])
    query = parse_qs(url.query)
    assert f"{url.scheme}://{url.netloc}{url.path}" == auth.GOOGLE_AUTH_URL
    assert query["client_id"] == [CLIENT_ID] and query["response_type"] == ["code"]
    assert set(query["scope"][0].split()) == {"openid", "email"}
    assert query["code_challenge_method"] == ["S256"] and query["state"][0] and query["code_challenge"][0]
    cookie = r.headers["set-cookie"].lower()
    assert "httponly" in cookie and "samesite=lax" in cookie and "secure" in cookie


def test_a_good_callback_creates_a_hashed_session_and_me_answers(client, caplog):
    with caplog.at_level(logging.DEBUG):
        r, route, query = _callback(client, {"id_token": _id_token(), "access_token": "ya29.secret"})
    assert r.status_code in (302, 303, 307)
    sent = parse_qs(route.calls.last.request.content.decode())
    verifier = sent["code_verifier"][0]
    assert sent["code"] == [CODE] and sent["client_secret"] == ["client-secret"]
    challenge = base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).rstrip(b"=").decode()
    assert query["code_challenge"] == [challenge]

    cookie = next(c for c in r.headers.get_list("set-cookie") if c.startswith(auth.SESSION_COOKIE + "="))
    low = cookie.lower()
    assert "httponly" in low and "secure" in low and "samesite=lax" in low
    raw = cookie.split(";", 1)[0].split("=", 1)[1]
    with store._connect() as db:
        stored = [row[0] for row in db.execute("SELECT token_sha256 FROM sessions")]
    assert stored == [hashlib.sha256(raw.encode()).hexdigest()]

    me = client.get("/api/auth/me").json()
    assert me["email"] == EMAIL and me["runs_left_today"] == auth.runs_per_day() == 1 and me["resets_at"]
    logged = "\n".join(rec.getMessage() for rec in caplog.records)
    assert CODE not in logged and raw not in logged and EMAIL not in logged and "ya29" not in logged


def test_logout_deletes_the_session(client):
    _callback(client, {"id_token": _id_token()})
    assert client.get("/api/auth/me").status_code == 200
    assert client.post("/api/auth/logout").status_code == 204
    with store._connect() as db:
        assert db.execute("SELECT COUNT(*) FROM sessions").fetchone()[0] == 0
    assert client.get("/api/auth/me").status_code == 401


def test_the_same_google_account_signs_in_to_the_same_user(client):
    _callback(client, {"id_token": _id_token()})
    _callback(client, {"id_token": _id_token(email="nuevo@example.com")})
    with store._connect() as db:
        assert tuple(db.execute("SELECT COUNT(*), MAX(email) FROM users").fetchone()) == (1, "nuevo@example.com")


@pytest.mark.parametrize("case", ["wrong_state", "google_error", "wrong_aud", "wrong_iss", "unverified", "expired", "no_id_token"])
def test_a_bad_callback_creates_no_session(client, case):
    token = {"id_token": _id_token()}
    state, params = None, {}
    if case == "wrong_state":
        state = "not-the-state"
    elif case == "google_error":
        params = {"error": "access_denied"}
    elif case == "wrong_aud":
        token = {"id_token": _id_token(aud="someone-else")}
    elif case == "wrong_iss":
        token = {"id_token": _id_token(iss="https://evil.example")}
    elif case == "unverified":
        token = {"id_token": _id_token(email_verified=False)}
    elif case == "expired":
        token = {"id_token": _id_token(exp=int(time.time()) - 10)}
    elif case == "no_id_token":
        token = {"access_token": "x"}
    r, _, _ = _callback(client, token, state=state, **params)
    assert r.status_code == 400 and "Google" in r.json()["detail"]
    assert not any(c.startswith(auth.SESSION_COOKIE + "=") for c in r.headers.get_list("set-cookie"))
    assert client.get("/api/auth/me").status_code == 401
    with store._connect() as db:
        assert db.execute("SELECT COUNT(*) FROM sessions").fetchone()[0] == 0


def test_without_a_google_client_sign_in_says_it_is_not_configured(client, monkeypatch):
    monkeypatch.setattr(settings, "GOOGLE_CLIENT_ID", None)
    r = client.get("/api/auth/google/login", follow_redirects=False)
    assert r.status_code == 503 and "Google" in r.json()["detail"]


def test_an_expired_session_is_not_accepted(client, monkeypatch):
    _callback(client, {"id_token": _id_token()})
    monkeypatch.setattr(auth.time, "time", lambda: time.time_ns() / 1e9 + auth.SESSION_SECONDS + 60)
    assert client.get("/api/auth/me").status_code == 401


def test_an_old_database_gains_the_owner_columns_and_still_creates_runs(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "DATA_DIR", tmp_path)
    with sqlite3.connect(tmp_path / "speedhack.db") as db:
        db.execute("CREATE TABLE projects (id TEXT PRIMARY KEY, mode TEXT NOT NULL, idea TEXT NOT NULL,"
                   " stack_prefs TEXT NOT NULL, demo_data INTEGER NOT NULL DEFAULT 0)")
        db.execute("INSERT INTO projects VALUES ('prj_old', 'dev', 'idea vieja', '[]', 0)")
    _, run = store.create_run(Mode.dev, "SaaS de gastos", [], demo_data=False)
    with sqlite3.connect(tmp_path / "speedhack.db") as db:
        columns = {row[1] for row in db.execute("PRAGMA table_info(projects)")}
        assert {"owner_id", "created"} <= columns
        assert db.execute("SELECT owner_id FROM projects WHERE id='prj_old'").fetchone() == (None,)
    assert store.get_project(run.project_id).idea == "SaaS de gastos"


@pytest.mark.parametrize("base_url, public_url, secure", [
    ("http://localhost:8000", None, False),  # Safari drops Secure cookies on http://localhost: state would mismatch
    ("http://127.0.0.1:8000", None, False),
    ("http://localhost:8000", "https://speedhack.example", True),
    ("http://speedhack.example", None, True),
])
def test_cookies_are_secure_except_on_plain_http_loopback(client, monkeypatch, base_url, public_url, secure):
    monkeypatch.setattr(settings, "PUBLIC_URL", public_url)
    local = TestClient(app, base_url=base_url)
    r = local.get("/api/auth/google/login", follow_redirects=False)
    assert ("secure" in r.headers["set-cookie"].lower()) is secure
