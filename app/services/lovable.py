"""Lovable adapter: build, database, publish, change and unpublish through Lovable's MCP server (ADR 0003).

The only module that talks to https://mcp.lovable.dev (a research preview: tools may change). It is a thin
layer over the official `mcp` SDK client (streamable HTTP). The bearer token comes from an injected async
`token_provider` (HACK-083 supplies the owner's real, refreshed one); the session comes from an injected
`session_factory(token)`, so tests use a fake session and never touch the network.

Tools used (names and arguments checked against the server's tool list on 2026-10-31):
- build:        `create_project(initial_message, workspace_id?, wait=True, timeout_seconds)`
- add_database: `enable_database(project_id)`
- publish:      `deploy_project(project_id, name?)`  (live URL on `*.lovable.app`)
- change:       `send_message(project_id, message, wait=True, timeout_seconds)`, then publish

`unpublish`: neither the HACK-068 spike's tool list nor the server's current list has an unpublish or
undeploy tool. The closest is `set_project_visibility`, and `unpublish` uses it with `private` (the
deprecated alias of `restricted`, which needs a Business plan). Its description only covers who can open
the project in the editor, so the `*.lovable.app` site may stay reachable: an open question for Dylan.

Contract: `awaiting_input` (a tool approval or a secret form) raises `LovableNeedsInput` and nothing
answers it; any error or timeout raises `LovableError`; with `DEMO_MODE` or no token every call raises
`LovableUnavailable`. Credits come only from Lovable's `cost_credits`, never estimated. No log line holds
a prompt, a URL or the token.
"""

from __future__ import annotations

import asyncio
import json
import logging
import time
from collections.abc import AsyncIterator, Awaitable, Callable
from contextlib import AbstractAsyncContextManager, asynccontextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol

from pydantic_settings import BaseSettings, SettingsConfigDict

from app.config import settings

log = logging.getLogger(__name__)

FIXTURES_DIR = Path(__file__).resolve().parent.parent / "fixtures" / "lovable"
MAX_SERVER_WAIT_S = 600  # create_project / send_message `timeout_seconds` maximum
UNPUBLISH_VISIBILITY = "private"
URL_KEYS = ("url", "live_url", "published_url", "deployed_url")


class _LovableEnv(BaseSettings):
    """Lovable settings from `.env`; they live here until app/config.py declares them."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    LOVABLE_MCP_URL: str = "https://mcp.lovable.dev"
    LOVABLE_BUILD_TIMEOUT: float = 600


lovable_env = _LovableEnv()


class LovableError(Exception):
    """A Lovable call failed, timed out or returned something unusable."""


class LovableUnavailable(LovableError):
    """DEMO_MODE, or no Lovable connection (token provider): nothing was sent."""


class LovableNeedsInput(LovableError):
    """The agent paused for a tool approval or a secret. SpeedHack never answers it."""


@dataclass(frozen=True)
class Build:
    project_id: str
    preview_url: str | None
    credits: float | None  # Lovable's `cost_credits`; None when it did not report one
    editor_url: str | None = None
    demo_data: bool = False


@dataclass(frozen=True)
class Change:
    credits: float | None
    url: str


class Session(Protocol):
    """What the adapter needs from an MCP client session (`mcp.ClientSession` satisfies it)."""

    async def call_tool(self, name: str, arguments: dict[str, Any]) -> Any: ...


TokenProvider = Callable[[], Awaitable[str | None]]
SessionFactory = Callable[[str], AbstractAsyncContextManager[Session]]


@asynccontextmanager
async def _mcp_session(token: str) -> AsyncIterator[Session]:
    """Default factory: a real MCP session over streamable HTTP with a bearer token."""
    from mcp import ClientSession
    from mcp.client.streamable_http import streamablehttp_client

    headers = {"Authorization": f"Bearer {token}"}
    async with streamablehttp_client(lovable_env.LOVABLE_MCP_URL, headers=headers) as (read, write, _):  # noqa: SIM117
        async with ClientSession(read, write) as session:
            await session.initialize()
            yield session


def _payload(result: Any, tool: str) -> dict[str, Any]:
    """The tool's JSON object, from a plain dict, `structuredContent` or JSON text content."""
    if isinstance(result, dict):
        return result
    if getattr(result, "isError", False):
        raise LovableError(f"{tool} returned an error")
    data = getattr(result, "structuredContent", None)
    if not data:
        for part in getattr(result, "content", None) or []:
            text = getattr(part, "text", None)
            if text:
                try:
                    data = json.loads(text)
                except ValueError:
                    data = None
                break
    if data is None:
        data = {}
    if not isinstance(data, dict):
        raise LovableError(f"{tool} returned an unreadable result")
    return data


def _status(data: dict[str, Any]) -> str | None:
    agent = data.get("agent_response")
    status = agent.get("status") if isinstance(agent, dict) else None
    return status or data.get("status")


def _check(data: dict[str, Any], tool: str) -> None:
    if _status(data) == "awaiting_input" or data.get("awaiting_input") or (
        isinstance(data.get("agent_response"), dict) and data["agent_response"].get("awaiting_input")
    ):
        raise LovableNeedsInput(f"{tool}: the agent is waiting for a human decision")
    status = _status(data)
    if status in ("error", "stopped", "failed", "in_progress"):
        raise LovableError(f"{tool}: the agent ended with status {status}")


def _credits(data: dict[str, Any]) -> float | None:
    for source in (data, data.get("agent_response")):
        if isinstance(source, dict) and isinstance(source.get("cost_credits"), (int, float)):
            return float(source["cost_credits"])
    return None


def _build(data: dict[str, Any], demo_data: bool = False) -> Build:
    project_id = data.get("projectId") or data.get("project_id")
    if not project_id:
        raise LovableError("create_project returned no project id")
    return Build(
        project_id=str(project_id),
        preview_url=data.get("preview_url"),
        credits=_credits(data),
        editor_url=data.get("editor_url"),
        demo_data=demo_data,
    )


def recorded_build() -> Build:
    """The recorded `create_project` result (labeled `demo_data`), for demos and tests."""
    data = json.loads((FIXTURES_DIR / "create_project.json").read_text(encoding="utf-8"))
    return _build(data, demo_data=bool(data.get("demo_data")))


class LovableAdapter:
    def __init__(self, token_provider: TokenProvider | None = None, session_factory: SessionFactory | None = None):
        self._token_provider = token_provider
        self._session_factory = session_factory or _mcp_session

    async def _call(self, step: str, tool: str, arguments: dict[str, Any], timeout: float | None = None) -> dict[str, Any]:
        if settings.DEMO_MODE or self._token_provider is None:
            raise LovableUnavailable("Lovable is not connected")
        token = await self._token_provider()
        if not token:
            raise LovableUnavailable("Lovable is not connected")
        started = time.monotonic()

        async def call() -> Any:
            async with self._session_factory(token) as session:
                return await session.call_tool(tool, arguments)

        try:
            result = await asyncio.wait_for(call(), timeout)
            data = _payload(result, tool)
            _check(data, tool)
        except LovableError as exc:
            log.warning("lovable step=%s outcome=%s duration=%.1fs", step, type(exc).__name__, time.monotonic() - started)
            raise
        except TimeoutError as exc:
            log.warning("lovable step=%s outcome=timeout duration=%.1fs", step, time.monotonic() - started)
            raise LovableError(f"{tool}: timed out after {timeout:g}s") from exc
        except Exception as exc:  # transport, protocol or SDK failure: never leak its text (it may echo the request)
            log.warning("lovable step=%s outcome=%s duration=%.1fs", step, type(exc).__name__, time.monotonic() - started)
            raise LovableError(f"{tool}: {type(exc).__name__}") from exc
        log.info("lovable step=%s outcome=ok duration=%.1fs credits=%s", step, time.monotonic() - started, _credits(data))
        return data

    async def build(self, prompt: str, workspace_id: str | None = None) -> Build:
        """`create_project`, waiting at most LOVABLE_BUILD_TIMEOUT seconds for the first build to finish."""
        timeout = lovable_env.LOVABLE_BUILD_TIMEOUT
        arguments: dict[str, Any] = {
            "initial_message": prompt,
            "wait": True,
            "timeout_seconds": max(1, min(int(timeout), MAX_SERVER_WAIT_S)),
        }
        if workspace_id:
            arguments["workspace_id"] = workspace_id
        data = await self._call("build", "create_project", arguments, timeout)
        build = _build(data)
        log.info("lovable step=build project=%s", build.project_id)
        return build

    async def add_database(self, project_id: str) -> None:
        """`enable_database`: provisions the project's PostgreSQL (30 to 60 s)."""
        await self._call("database", "enable_database", {"project_id": project_id}, MAX_SERVER_WAIT_S)

    async def publish(self, project_id: str, name: str | None = None) -> str:
        """`deploy_project`: returns the live `*.lovable.app` URL."""
        arguments: dict[str, Any] = {"project_id": project_id}
        if name:
            arguments["name"] = name
        data = await self._call("publish", "deploy_project", arguments, MAX_SERVER_WAIT_S)
        url = next((data[key] for key in URL_KEYS if isinstance(data.get(key), str) and data[key]), None)
        if not url:
            raise LovableError("deploy_project returned no URL")
        return url

    async def change(self, project_id: str, text: str) -> Change:
        """`send_message` and wait for the agent, then publish the new version."""
        arguments = {
            "project_id": project_id,
            "message": text,
            "wait": True,
            "timeout_seconds": MAX_SERVER_WAIT_S,
        }
        data = await self._call("change", "send_message", arguments, lovable_env.LOVABLE_BUILD_TIMEOUT)
        return Change(credits=_credits(data), url=await self.publish(project_id))

    async def unpublish(self, project_id: str) -> None:
        """No unpublish tool exists (see module docstring): `set_project_visibility` private."""
        arguments = {"project_id": project_id, "visibility": UNPUBLISH_VISIBILITY}
        await self._call("unpublish", "set_project_visibility", arguments, MAX_SERVER_WAIT_S)


_adapter = LovableAdapter()


def configure(token_provider: TokenProvider | None, session_factory: SessionFactory | None = None) -> None:
    """HACK-083 plugs the owner's token provider in here at startup."""
    global _adapter
    _adapter = LovableAdapter(token_provider, session_factory)


async def build(prompt: str, workspace_id: str | None = None) -> Build:
    return await _adapter.build(prompt, workspace_id)


async def add_database(project_id: str) -> None:
    await _adapter.add_database(project_id)


async def publish(project_id: str, name: str | None = None) -> str:
    return await _adapter.publish(project_id, name)


async def change(project_id: str, text: str) -> Change:
    return await _adapter.change(project_id, text)


async def unpublish(project_id: str) -> None:
    await _adapter.unpublish(project_id)
