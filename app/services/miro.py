"""Miro service: builds the architecture board item by item (REST API v2)."""
from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Any, AsyncIterator, Awaitable, Callable, Dict, Optional

import httpx

from app.config import settings
from app.schemas.content import Architecture

API = "https://api.miro.com/v2"
FIXTURE = Path(__file__).parent.parent / "fixtures" / "miro" / "demo_board.json"
MAX_RETRIES = 5

COLORS = {"screen": "#fff9b1", "data_model": "#c6dcff", "integration": "#d5f692"}
MIRO_COLORS = {"screen": "yellow", "data_model": "light_blue", "integration": "light_green"}
FRAMES = [  # (architecture field, item kind, frame title)
    ("screens", "screen", "Pantallas"),
    ("data_model", "data_model", "Modelo de datos"),
    ("integrations", "integration", "Integraciones"),
]
FRAME_W, FRAME_H, FRAME_GAP = 520, 700, 120
NOTE, NOTE_GAP = 200, 40

Sleep = Callable[[float], Awaitable[None]]


class MiroError(RuntimeError):
    pass


class BoardRun:
    """Async-iterable of `miro_item` payloads; `embed_url` is set once exhausted.

    `ids` maps a stable key to the Miro id already created, so a retry with the
    same dict never duplicates items.
    """

    def __init__(
        self,
        architecture: Architecture,
        *,
        demo: Optional[bool] = None,
        ids: Optional[Dict[str, str]] = None,
        client: Optional[httpx.AsyncClient] = None,
        sleep: Sleep = asyncio.sleep,
    ) -> None:
        self.architecture = architecture
        self.demo = settings.DEMO_MODE if demo is None else demo
        self.ids = ids if ids is not None else {}
        self.embed_url: Optional[str] = None
        self._client = client
        self._sleep = sleep

    def __aiter__(self) -> AsyncIterator[Dict[str, Any]]:
        return self._demo() if self.demo else self._live()

    async def _demo(self) -> AsyncIterator[Dict[str, Any]]:
        data = json.loads(FIXTURE.read_text())
        self.embed_url = data["embed_url"]
        for item in data["items"]:
            await self._sleep(item.get("delay", 0))
            payload = {k: v for k, v in item.items() if k != "delay"}
            yield {**payload, "demo_data": True}

    async def _request(self, client: httpx.AsyncClient, method: str, path: str, **kw: Any) -> Dict[str, Any]:
        for attempt in range(MAX_RETRIES):
            r = await client.request(method, f"{API}{path}", **kw)
            if r.status_code != 429:
                if r.status_code >= 400:
                    raise MiroError(f"{method} {path} -> {r.status_code}: {r.text[:200]}")
                return r.json()
            await self._sleep(float(r.headers.get("Retry-After", 2**attempt)))
        raise MiroError(f"{method} {path}: still 429 after {MAX_RETRIES} retries")

    async def _live(self) -> AsyncIterator[Dict[str, Any]]:
        if not settings.MIRO_ACCESS_TOKEN:
            raise MiroError("MIRO_ACCESS_TOKEN is not set")
        own = self._client is None
        client = self._client or httpx.AsyncClient(
            headers={"Authorization": f"Bearer {settings.MIRO_ACCESS_TOKEN}"}, timeout=30
        )
        try:
            if "board" not in self.ids:
                board = await self._request(client, "POST", "/boards", json={"name": "SpeedHack · arquitectura"})
                self.ids["board"] = board["id"]
            board_id = self.ids["board"]
            self.embed_url = f"https://miro.com/app/live-embed/{board_id}/"
            frame_ids = []
            for col, (field, kind, title) in enumerate(FRAMES):
                fx = col * (FRAME_W + FRAME_GAP)
                fkey = f"frame:{kind}"
                if fkey not in self.ids:
                    f = await self._request(
                        client, "POST", f"/boards/{board_id}/frames",
                        json={
                            "data": {"title": title, "format": "custom"},
                            "position": {"x": fx, "y": 0},
                            "geometry": {"width": FRAME_W, "height": FRAME_H},
                        },
                    )
                    self.ids[fkey] = f["id"]
                    yield _event("frame", title, f["id"], fx, 0, FRAME_W, FRAME_H, "#e6e6e6")
                frame_ids.append(self.ids[fkey])
                for row, text in enumerate(getattr(self.architecture, field)):
                    nkey = f"{kind}:{text}"
                    if nkey in self.ids:
                        continue
                    # position is relative to the parent frame's top-left corner
                    rx, ry = FRAME_W / 2, NOTE / 2 + NOTE_GAP + row * (NOTE + NOTE_GAP)
                    n = await self._request(
                        client, "POST", f"/boards/{board_id}/sticky_notes",
                        json={
                            "data": {"content": text, "shape": "square"},
                            "style": {"fillColor": MIRO_COLORS[kind]},
                            "position": {"x": rx, "y": ry},
                            "geometry": {"width": NOTE},
                            "parent": {"id": self.ids[fkey]},
                        },
                    )
                    self.ids[nkey] = n["id"]
                    yield _event(kind, text, n["id"], fx, ry - FRAME_H / 2, NOTE, NOTE, COLORS[kind])
            for a, b in zip(frame_ids, frame_ids[1:]):
                ckey = f"connector:{a}:{b}"
                if ckey in self.ids:
                    continue
                c = await self._request(
                    client, "POST", f"/boards/{board_id}/connectors",
                    json={"startItem": {"id": a}, "endItem": {"id": b}},
                )
                self.ids[ckey] = c["id"]
                yield _event("connector", f"{a} -> {b}", c["id"], 0, 0, 0, 0, "#1a1a1a")
        finally:
            if own:
                await client.aclose()


def _event(kind: str, title: str, miro_id: str, x: float, y: float, w: float, h: float, color: str) -> Dict[str, Any]:
    return {"kind": kind, "title": title, "miro_id": miro_id, "x": x, "y": y, "w": w, "h": h, "color": color}


def build_board(architecture: Architecture, **kw: Any) -> BoardRun:
    """Iterate to get one `miro_item` payload per item; read `.embed_url` afterwards."""
    return BoardRun(architecture, **kw)
