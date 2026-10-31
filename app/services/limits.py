"""Quotas and rate limits (spec 001): projects per user and per day, projects per day for everyone, requests per minute.

All of it is behind AUTH_REQUIRED, like ownership. A refusal never reaches a provider, creates nothing and logs the
user id, the route template and a reason category: never the idea, the answers, the email or a token.
"""
from __future__ import annotations

import datetime as dt
import logging
import math
import threading
import time
from collections import defaultdict, deque
from contextlib import closing
from typing import Any

from fastapi import Cookie, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic_settings import BaseSettings, SettingsConfigDict

from app.services import auth, store

log = logging.getLogger(__name__)

WINDOW_SECONDS = 60
SWEEP_AT = 2048  # idle buckets are dropped once this many exist


class _LimitEnv(BaseSettings):
    """Read from the environment on its own, like `llm.gemini_env`, so `config.py` stays untouched."""
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    MAX_PROJECTS_PER_DAY: int = 5  # new projects per UTC day, everyone together
    REQUESTS_PER_MINUTE: int = 30  # per route and user


env = _LimitEnv()
clock = time.monotonic  # tests replace it to move the window
project_gate = threading.Lock()  # counting and creating happen under it, so two requests cannot both take the last slot
_hits: dict[tuple[str, str], deque[float]] = defaultdict(deque)
_hits_lock = threading.Lock()


def reset() -> None:
    with _hits_lock:
        _hits.clear()


def _log(status: int, request: Request, user: dict[str, Any] | None, reason: str) -> None:
    route = getattr(request.scope.get("route"), "path", request.url.path)  # the template, never ids or the body
    log.info("refused %s route=%s user=%s reason=%s", status, route, user["id"] if user else "-", reason)


# --- Projects per day -------------------------------------------------------------------------------------------


def _projects_today() -> int:
    with closing(store._connect()) as conn:
        return conn.execute("SELECT COUNT(*) FROM projects WHERE created>=?", (auth.day_window()[0],)).fetchone()[0]


def _used_today(user: dict[str, Any]) -> int:
    return store.projects_since(user["id"], auth.day_window()[0])


def runs_left(user: dict[str, Any]) -> int:
    """New projects this user can still create today: their own quota or what is left of the global cap, the smaller."""
    own = auth.runs_per_day() - _used_today(user)
    everyone = env.MAX_PROJECTS_PER_DAY - _projects_today()
    return max(0, min(own, everyone))


def _reset_text(resets_at: str) -> str:
    return f"{dt.datetime.fromisoformat(resets_at):%Y-%m-%d} 00:00 UTC"


def _refusal(status: int, request: Request, user: dict[str, Any], reason: str, message: str, **extra: Any) -> JSONResponse:
    _log(status, request, user, reason)
    resets_at = auth.day_window()[1]
    wait = max(1, math.ceil(dt.datetime.fromisoformat(resets_at).timestamp() - time.time()))
    return JSONResponse(
        {"detail": message.format(reset=_reset_text(resets_at)), "resets_at": resets_at, **extra},
        status_code=status, headers={"Retry-After": str(wait)},
    )


def new_project_refusal(request: Request, user: dict[str, Any] | None) -> JSONResponse | None:
    """The 429 / 503 answer for a new project, or None when it may go ahead. Call it holding `project_gate`."""
    if not auth.required() or user is None:
        return None
    limit, used = auth.runs_per_day(), _used_today(user)
    if used >= limit:
        return _refusal(
            429, request, user, "quota",
            f"Ya creaste {used} {'proyecto' if used == 1 else 'proyectos'} hoy (el límite es {limit} al día). "
            "Podrás crear otro a partir de {reset}.",
            used=used, limit=limit,
        )
    cap = env.MAX_PROJECTS_PER_DAY
    if _projects_today() >= cap:
        return _refusal(
            503, request, user, "global cap",
            f"Hoy se alcanzó el límite de proyectos nuevos de SpeedHack ({cap} al día entre todas las personas). "
            "Los proyectos en curso siguen funcionando. Vuelve a intentarlo a partir de {reset}.",
            limit=cap,
        )
    return None


# --- Requests per minute ----------------------------------------------------------------------------------------


def throttle(request: Request, sh_session: str | None = Cookie(default=None)) -> None:
    """Dependency: at most REQUESTS_PER_MINUTE requests per route and user (per client address while anonymous)."""
    if not auth.required():
        return
    user = auth.user_for(sh_session)
    route = getattr(request.scope.get("route"), "path", request.url.path)
    who = user["id"] if user else f"ip:{request.client.host if request.client else '-'}"
    now = clock()
    with _hits_lock:
        if len(_hits) > SWEEP_AT:
            for key in [k for k, q in _hits.items() if not q or q[-1] <= now - WINDOW_SECONDS]:
                del _hits[key]
        hits = _hits[(who, route)]
        while hits and hits[0] <= now - WINDOW_SECONDS:
            hits.popleft()
        if len(hits) >= env.REQUESTS_PER_MINUTE:
            wait = max(1, math.ceil(hits[0] + WINDOW_SECONDS - now)) if hits else WINDOW_SECONDS
        else:
            hits.append(now)
            return
    _log(429, request, user, "rate limit")
    raise HTTPException(
        429, f"Demasiadas solicitudes: el máximo es {env.REQUESTS_PER_MINUTE} por minuto en esta ruta. "
        f"Vuelve a intentarlo en {wait} s.", headers={"Retry-After": str(wait)},
    )
