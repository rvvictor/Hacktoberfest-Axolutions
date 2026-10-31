"""Sign in with Google (spec 001): OpenID Connect code flow with PKCE and `state`, opaque hashed sessions.

The `id_token` arrives straight from Google's token endpoint over TLS, so OIDC Core §3.1.3.7 lets the client
skip its signature; `iss`, `aud`, `exp` and `email_verified` are still checked. Only the session token's SHA-256
is stored. Nothing here logs a code, a token or an email.
"""
from __future__ import annotations

import base64
import binascii
import datetime as dt
import hashlib
import hmac
import json
import logging
import secrets
import time
from contextlib import closing
from typing import Any
from urllib.parse import urlencode

import httpx
from fastapi import Cookie, HTTPException, Request

from app.config import Settings, settings
from app.services import store

log = logging.getLogger(__name__)

GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_ISSUERS = {"https://accounts.google.com", "accounts.google.com"}
SESSION_COOKIE = "sh_session"
FLOW_COOKIE = "sh_oauth"  # state and PKCE verifier of a sign-in in progress
FLOW_SECONDS = 600
SESSION_SECONDS = 30 * 24 * 3600
FAILED = "No pudimos iniciar sesión con Google. Vuelve a intentarlo."
SIGN_IN = "Inicia sesión para continuar."
OWNER_ONLY = "Solo la persona dueña del sitio puede usar esto."


class AuthError(Exception):
    """A sign-in that must not create a session; the message is safe to show (Spanish)."""

    def __init__(self, reason: str, message: str = FAILED):
        super().__init__(message)
        self.reason = reason  # for logs: a category, never the code, token or email


def configured() -> bool:
    return bool(settings.GOOGLE_CLIENT_ID and settings.GOOGLE_CLIENT_SECRET)


def _sha256(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


def new_flow() -> tuple[str, str, str]:
    """(state, PKCE verifier, S256 challenge) for one sign-in."""
    state, verifier = secrets.token_urlsafe(24), secrets.token_urlsafe(48)
    challenge = base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).rstrip(b"=").decode()
    return state, verifier, challenge


def authorize_url(redirect_uri: str, state: str, challenge: str) -> str:
    return GOOGLE_AUTH_URL + "?" + urlencode({
        "client_id": settings.GOOGLE_CLIENT_ID, "redirect_uri": redirect_uri, "response_type": "code",
        "scope": "openid email", "state": state, "code_challenge": challenge, "code_challenge_method": "S256",
        "prompt": "select_account",
    })


def same_state(expected: str, received: str) -> bool:
    return bool(expected and received) and hmac.compare_digest(expected, received)


def _claims(id_token: str) -> dict[str, Any]:
    try:
        payload = id_token.split(".")[1]
        return json.loads(base64.urlsafe_b64decode(payload + "=" * (-len(payload) % 4)))
    except (IndexError, ValueError, binascii.Error) as exc:
        raise AuthError("malformed id_token") from exc


def exchange(code: str, verifier: str, redirect_uri: str) -> dict[str, Any]:
    """Trade the code for Google's claims; raises AuthError unless they name a verified email for this client."""
    try:
        r = httpx.post(GOOGLE_TOKEN_URL, timeout=10, data={
            "code": code, "client_id": settings.GOOGLE_CLIENT_ID, "client_secret": settings.GOOGLE_CLIENT_SECRET,
            "redirect_uri": redirect_uri, "grant_type": "authorization_code", "code_verifier": verifier,
        })
    except httpx.HTTPError as exc:
        raise AuthError("token endpoint unreachable") from exc
    try:
        id_token = r.json().get("id_token") if r.status_code == 200 else None
    except ValueError:
        id_token = None
    if not isinstance(id_token, str):
        raise AuthError(f"token endpoint {r.status_code}")
    claims = _claims(id_token)
    if claims.get("iss") not in GOOGLE_ISSUERS:
        raise AuthError("wrong iss")
    if claims.get("aud") != settings.GOOGLE_CLIENT_ID:
        raise AuthError("wrong aud")
    if not isinstance(claims.get("exp"), (int, float)) or claims["exp"] <= time.time():
        raise AuthError("expired id_token")
    if claims.get("email_verified") is not True or not claims.get("email") or not claims.get("sub"):
        raise AuthError("unverified email")
    return claims


def start_session(claims: dict[str, Any]) -> str:
    """Create the user on first sign-in and a session; returns the raw token for the cookie (stored hashed)."""
    user_id = store.upsert_user(str(claims["sub"]), str(claims["email"]))
    token = secrets.token_urlsafe(32)
    store.add_session(_sha256(token), user_id, time.time() + SESSION_SECONDS)
    return token


def user_for(token: str | None) -> dict[str, Any] | None:
    return store.session_user(_sha256(token), time.time()) if token else None


def end_session(token: str | None) -> None:
    if token:
        store.delete_session(_sha256(token))


def day_window(now: float | None = None) -> tuple[float, str]:
    """Start of the current UTC day (epoch) and the next reset as ISO 8601."""
    today = dt.datetime.fromtimestamp(now if now is not None else time.time(), dt.UTC).replace(
        hour=0, minute=0, second=0, microsecond=0)
    return today.timestamp(), (today + dt.timedelta(days=1)).isoformat()


def runs_per_day() -> int:
    # The test configuration resets every setting to None; fall back to the declared default.
    value = settings.RUNS_PER_USER_PER_DAY
    return Settings.model_fields["RUNS_PER_USER_PER_DAY"].default if value is None else value


def me(user: dict[str, Any]) -> dict[str, Any]:
    start, resets_at = day_window()
    used = store.projects_since(user["id"], start)
    return {"email": user["email"], "runs_left_today": max(0, runs_per_day() - used), "resets_at": resets_at}


# --- Ownership (spec 001, HACK-077). Everything below is a no-op while AUTH_REQUIRED is false. ---


def required() -> bool:
    return bool(settings.AUTH_REQUIRED)  # the test configuration sets it to None


def is_owner(user: dict[str, Any] | None) -> bool:
    owner = (settings.OWNER_EMAIL or "").strip().lower()
    return bool(user and owner and str(user["email"]).strip().lower() == owner)


def set_owner(project_id: str, user_id: str) -> None:
    with closing(store._connect()) as conn, conn:
        conn.execute("UPDATE projects SET owner_id=? WHERE id=?", (user_id, project_id))


def run_owner(run_id: str) -> tuple[bool, str | None]:
    """(the run exists, its project's owner_id); legacy projects have owner_id NULL."""
    with closing(store._connect()) as conn:
        row = conn.execute(
            "SELECT p.owner_id AS owner_id FROM runs r JOIN projects p ON p.id = r.project_id WHERE r.run_id=?",
            (run_id,),
        ).fetchone()
    return (row is not None), (row["owner_id"] if row else None)


def _refuse(request: Request, status: int, detail: str, reason: str, user: dict[str, Any] | None = None) -> HTTPException:
    route = getattr(request.scope.get("route"), "path", request.url.path)  # the template, never the ids or the body
    log.info("refused %s route=%s user=%s reason=%s", status, route, user["id"] if user else "-", reason)
    return HTTPException(status, detail)


def _authenticate(request: Request, token: str | None) -> dict[str, Any]:
    user = user_for(token)
    if user is None:
        raise _refuse(request, 401, SIGN_IN, "no session")
    return user


def current_user(request: Request, sh_session: str | None = Cookie(default=None)) -> dict[str, Any] | None:
    """The signed-in user; 401 without a session when AUTH_REQUIRED, otherwise anonymous (None) is fine."""
    return _authenticate(request, sh_session) if required() else user_for(sh_session)


def own_run(unknown: str | None = None, public_run: str | None = None):
    """Dependency factory for routes with `{run_id}`: 401 without a session, 404 (the unknown-run answer) if not yours.

    `unknown` is the route's own 404 message; `public_run` is the recorded example, open while DEMO_MODE is on.
    """
    def dependency(run_id: str, request: Request, sh_session: str | None = Cookie(default=None)) -> str:
        if not required() or (public_run and run_id == public_run and settings.DEMO_MODE):
            return run_id
        user = _authenticate(request, sh_session)
        exists, owner = run_owner(run_id)
        if not exists or not (owner == user["id"] or (owner is None and is_owner(user))):
            raise _refuse(request, 404, unknown or f"run {run_id} not found", "unknown run" if not exists else "not owner", user)
        return run_id
    return dependency


def owner_only(request: Request, sh_session: str | None = Cookie(default=None)) -> None:
    """Hunter and Ops: 403 for everyone but OWNER_EMAIL (anonymous included)."""
    if not required():
        return
    user = user_for(sh_session)
    if not is_owner(user):
        raise _refuse(request, 403, OWNER_ONLY, "not the site owner", user)


def paid_voice(request: Request, sh_session: str | None = Cookie(default=None)) -> None:
    """Voice spends provider credit: a session is needed unless DEMO_MODE serves the recorded sample."""
    if required() and not settings.DEMO_MODE:
        _authenticate(request, sh_session)
