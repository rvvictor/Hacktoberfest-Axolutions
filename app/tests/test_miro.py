import asyncio
import functools

import httpx
import pytest
import respx

from app.config import settings
from app.schemas.content import Architecture
from app.services import miro

ARCH = Architecture(screens=["Login", "Dashboard"], data_model=["User"], integrations=["Stripe"])


def aio(fn):
    """Run an async test with asyncio.run (no pytest-asyncio in the project)."""

    @functools.wraps(fn)
    def wrapper(*a, **kw):
        return asyncio.run(fn(*a, **kw))

    return wrapper


async def _nosleep(_: float) -> None:
    pass


async def _collect(run):
    return [e async for e in run]


@aio
async def test_demo_yields_recorded_items_at_pace():
    waits = []

    async def sleep(s):
        waits.append(s)

    run = miro.build_board(ARCH, demo=True, sleep=sleep)
    items = await _collect(run)
    assert len(items) == 10 and all(i["demo_data"] for i in items)
    assert {"x", "y", "w", "h", "color"} <= items[3].keys()
    assert sum(waits) > 0
    assert run.embed_url.startswith("https://miro.com/app/live-embed/")


def _mock(router, counter):
    def make(prefix):
        def handler(request):
            counter[prefix] = counter.get(prefix, 0) + 1
            return httpx.Response(200, json={"id": f"{prefix}{counter[prefix]}"})
        return handler

    router.post("https://api.miro.com/v2/boards").mock(side_effect=make("b"))
    router.post(url__regex=r".*/frames$").mock(side_effect=make("f"))
    router.post(url__regex=r".*/sticky_notes$").mock(side_effect=make("n"))
    router.post(url__regex=r".*/connectors$").mock(side_effect=make("c"))


@aio
async def test_live_builds_items_and_retry_does_not_duplicate(monkeypatch):
    monkeypatch.setattr(settings, "MIRO_ACCESS_TOKEN", "test-token")
    ids, counter = {}, {}
    with respx.mock(assert_all_called=False) as router:
        _mock(router, counter)
        run = miro.build_board(ARCH, demo=False, ids=ids, sleep=_nosleep)
        first = await _collect(run)
        assert [e["kind"] for e in first].count("screen") == 2
        assert run.embed_url == "https://miro.com/app/live-embed/b1/"
        total = sum(counter.values())
        again = await _collect(miro.build_board(ARCH, demo=False, ids=ids, sleep=_nosleep))
        assert again == [] and sum(counter.values()) == total


@aio
async def test_retries_on_429_with_backoff(monkeypatch):
    monkeypatch.setattr(settings, "MIRO_ACCESS_TOKEN", "test-token")
    waits, calls = [], {"n": 0}

    async def sleep(s):
        waits.append(s)

    def board(request):
        calls["n"] += 1
        if calls["n"] < 3:
            return httpx.Response(429)
        return httpx.Response(200, json={"id": "b1"})

    arch = Architecture(screens=[], data_model=[], integrations=[])
    with respx.mock(assert_all_called=False) as router:
        router.post("https://api.miro.com/v2/boards").mock(side_effect=board)
        router.post(url__regex=r".*/frames$").mock(return_value=httpx.Response(200, json={"id": "f"}))
        router.post(url__regex=r".*/connectors$").mock(return_value=httpx.Response(200, json={"id": "c"}))
        await _collect(miro.build_board(arch, demo=False, sleep=sleep))
    assert waits[:2] == [1, 2]


@aio
async def test_gives_up_after_max_retries(monkeypatch):
    monkeypatch.setattr(settings, "MIRO_ACCESS_TOKEN", "test-token")
    with respx.mock() as router:
        router.post("https://api.miro.com/v2/boards").mock(return_value=httpx.Response(429))
        with pytest.raises(miro.MiroError):
            await _collect(miro.build_board(ARCH, demo=False, sleep=_nosleep))


BIG = Architecture(
    screens=["Login", "Dashboard", "Nuevo gasto", "Aprobaciones", "Alertas"],
    data_model=["Empresa", "Usuario"],
    integrations=["Supabase"],
)


@aio
async def test_every_note_fits_inside_its_frame(monkeypatch):
    """Miro answers 400 'outside of parent boundaries' for a note below its frame (live run, HACK-041)."""
    import json

    monkeypatch.setattr(settings, "MIRO_ACCESS_TOKEN", "test-token")
    with respx.mock(assert_all_called=False) as router:
        _mock(router, {})
        await _collect(miro.build_board(BIG, demo=False, ids={}, sleep=_nosleep))
        frames = [json.loads(c.request.content) for c in router.routes[1].calls]
        notes = [json.loads(c.request.content) for c in router.routes[2].calls]
    screens_frame = frames[0]["geometry"]["height"]
    lowest = max(n["position"]["y"] for n in notes) + miro.NOTE / 2
    assert screens_frame >= lowest + miro.NOTE_GAP  # 5 notes: taller than the old fixed 700 px
    assert screens_frame > miro.FRAME_H
    assert frames[2]["geometry"]["height"] == miro.FRAME_H  # one note: the usual size


@aio
async def test_rerun_with_more_notes_grows_the_frame_once(monkeypatch):
    monkeypatch.setattr(settings, "MIRO_ACCESS_TOKEN", "test-token")
    ids = {}
    with respx.mock(assert_all_called=False) as router:
        _mock(router, {})
        patch = router.patch(url__regex=r".*/frames/.*").mock(return_value=httpx.Response(200, json={}))
        await _collect(miro.build_board(ARCH, demo=False, ids=ids, sleep=_nosleep))
        await _collect(miro.build_board(BIG, demo=False, ids=ids, sleep=_nosleep))
        assert patch.call_count == 1  # only the screens frame needed more room
        await _collect(miro.build_board(BIG, demo=False, ids=ids, sleep=_nosleep))
        assert patch.call_count == 1  # already big enough: no further call


@aio
async def test_transient_server_error_is_retried(monkeypatch):
    monkeypatch.setattr(settings, "MIRO_ACCESS_TOKEN", "test-token")
    waits = []

    async def record(seconds):
        waits.append(seconds)

    with respx.mock(assert_all_called=False) as router:
        router.post("https://api.miro.com/v2/boards").mock(
            side_effect=[httpx.Response(500, json={"message": "Internal error occurred"}), httpx.Response(201, json={"id": "b1"})]
        )
        router.post(url__regex=r".*/(frames|sticky_notes|connectors)$").mock(return_value=httpx.Response(201, json={"id": "x"}))
        run = miro.build_board(Architecture(screens=["Login"], data_model=[], integrations=[]), demo=False, ids={}, sleep=record)
        await _collect(run)
    assert run.ids["board"] == "b1" and waits == [2.0]


@aio
async def test_persistent_server_error_still_fails(monkeypatch):
    monkeypatch.setattr(settings, "MIRO_ACCESS_TOKEN", "test-token")
    with respx.mock(assert_all_called=False) as router:
        route = router.post("https://api.miro.com/v2/boards").mock(return_value=httpx.Response(500))
        with pytest.raises(miro.MiroError):
            await _collect(miro.build_board(ARCH, demo=False, ids={}, sleep=_nosleep))
    assert route.call_count == 1 + miro.MAX_SERVER_RETRIES
