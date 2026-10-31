"""Lovable adapter (HACK-082): a fake MCP session stands in for https://mcp.lovable.dev; no test touches the network."""

import asyncio
import json
import logging
from contextlib import asynccontextmanager
from pathlib import Path
from types import SimpleNamespace

import pytest

from app.config import settings
from app.services import lovable

FIXTURES = Path(__file__).resolve().parent.parent / "fixtures" / "lovable"
PROMPT = "SECRET-PROMPT quiero una barberia"
TOKEN = "tok-SECRET-123"


def fixture(name: str) -> dict:
    return json.loads((FIXTURES / f"{name}.json").read_text(encoding="utf-8"))


class FakeSession:
    """Records every call and answers from `replies[tool]` (a payload, an Exception, or a callable)."""

    def __init__(self, replies: dict):
        self.replies = replies
        self.calls: list[tuple[str, dict]] = []

    async def call_tool(self, name: str, arguments: dict):
        self.calls.append((name, arguments))
        reply = self.replies[name]
        if callable(reply):
            reply = await reply()
        if isinstance(reply, Exception):
            raise reply
        return SimpleNamespace(isError=False, structuredContent=reply, content=[])


def make_adapter(session: FakeSession, token: str | None = TOKEN) -> lovable.LovableAdapter:
    seen_tokens: list[str] = []

    async def token_provider():
        return token

    @asynccontextmanager
    async def factory(tok: str):
        seen_tokens.append(tok)
        yield session

    adapter = lovable.LovableAdapter(token_provider=token_provider, session_factory=factory)
    adapter.seen_tokens = seen_tokens
    return adapter


@pytest.fixture(autouse=True)
def live(monkeypatch):
    monkeypatch.setattr(settings, "DEMO_MODE", False)


def run(coro):
    return asyncio.run(coro)


def test_awaiting_input_raises_needs_input_and_is_never_answered():
    session = FakeSession({"create_project": fixture("awaiting_input")})
    with pytest.raises(lovable.LovableNeedsInput):
        run(make_adapter(session).build(PROMPT))
    assert [name for name, _ in session.calls] == ["create_project"]  # no respond_to_approval, no send_message


def test_demo_mode_is_unavailable_without_opening_a_session():
    session = FakeSession({})
    settings.DEMO_MODE = True
    with pytest.raises(lovable.LovableUnavailable):
        run(make_adapter(session).build(PROMPT))
    assert session.calls == []


def test_no_token_provider_is_unavailable_with_no_network():
    with pytest.raises(lovable.LovableUnavailable):
        run(lovable.LovableAdapter().build(PROMPT))  # default factory would open https://mcp.lovable.dev


def test_token_provider_returning_nothing_is_unavailable():
    session = FakeSession({})
    with pytest.raises(lovable.LovableUnavailable):
        run(make_adapter(session, token=None).publish("p1"))
    assert session.calls == []


def test_every_operation_is_unavailable_in_demo_mode():
    settings.DEMO_MODE = True
    adapter = make_adapter(FakeSession({}))
    for call in (
        adapter.build(PROMPT),
        adapter.add_database("p1"),
        adapter.publish("p1"),
        adapter.change("p1", "x"),
        adapter.unpublish("p1"),
    ):
        with pytest.raises(lovable.LovableUnavailable):
            run(call)


def test_build_calls_create_project_and_reads_credits_from_cost_credits():
    session = FakeSession({"create_project": fixture("create_project")})
    adapter = make_adapter(session)
    build = run(adapter.build(PROMPT, workspace_id="ws-1"))
    (name, args), = session.calls
    assert name == "create_project"
    assert args["initial_message"] == PROMPT
    assert args["wait"] is True
    assert args["workspace_id"] == "ws-1"
    assert args["timeout_seconds"] == 600
    assert build.project_id == "3b7c2d67-adb0-45e1-befd-90ce66ad8776"
    assert build.preview_url == "https://id-preview--demo.lovable.app"
    assert build.credits == 2.2
    assert adapter.seen_tokens == [TOKEN]


def test_credits_are_none_when_lovable_reports_none_never_estimated():
    reply = fixture("create_project")
    del reply["cost_credits"]
    build = run(make_adapter(FakeSession({"create_project": reply})).build(PROMPT))
    assert build.credits is None


def test_credits_found_inside_agent_response_too():
    reply = fixture("create_project")
    reply["agent_response"]["cost_credits"] = reply.pop("cost_credits")
    build = run(make_adapter(FakeSession({"create_project": reply})).build(PROMPT))
    assert build.credits == 2.2


def test_build_without_workspace_omits_workspace_id():
    session = FakeSession({"create_project": fixture("create_project")})
    run(make_adapter(session).build(PROMPT))
    assert "workspace_id" not in session.calls[0][1]


def test_build_timeout_raises_lovable_error(monkeypatch):
    monkeypatch.setattr(lovable.lovable_env, "LOVABLE_BUILD_TIMEOUT", 0.05)

    async def hang():
        await asyncio.sleep(5)

    with pytest.raises(lovable.LovableError):
        run(make_adapter(FakeSession({"create_project": hang})).build(PROMPT))


def test_build_still_in_progress_at_the_server_timeout_is_an_error():
    reply = {"projectId": "p1", "agent_response": {"status": "in_progress", "message_id": "m1"}}
    with pytest.raises(lovable.LovableError):
        run(make_adapter(FakeSession({"create_project": reply})).build(PROMPT))


@pytest.mark.parametrize("status", ["error", "stopped"])
def test_build_agent_failure_raises_lovable_error(status):
    reply = {"projectId": "p1", "agent_response": {"status": status}}
    with pytest.raises(lovable.LovableError):
        run(make_adapter(FakeSession({"create_project": reply})).build(PROMPT))


def test_build_without_project_id_raises_lovable_error():
    reply = {"agent_response": {"status": "completed"}}
    with pytest.raises(lovable.LovableError):
        run(make_adapter(FakeSession({"create_project": reply})).build(PROMPT))


def test_tool_error_result_raises_lovable_error():
    class ErrorSession(FakeSession):
        async def call_tool(self, name, arguments):
            self.calls.append((name, arguments))
            return SimpleNamespace(isError=True, structuredContent=None, content=[SimpleNamespace(text="boom")])

    with pytest.raises(lovable.LovableError):
        run(make_adapter(ErrorSession({})).publish("p1"))


def test_transport_failure_is_wrapped_in_lovable_error():
    session = FakeSession({"deploy_project": ConnectionError("down")})
    with pytest.raises(lovable.LovableError):
        run(make_adapter(session).publish("p1"))


def test_result_can_arrive_as_json_text_content():
    class TextSession(FakeSession):
        async def call_tool(self, name, arguments):
            self.calls.append((name, arguments))
            text = SimpleNamespace(text=json.dumps(fixture("create_project")))
            return SimpleNamespace(isError=False, structuredContent=None, content=[text])

    assert run(make_adapter(TextSession({})).build(PROMPT)).credits == 2.2


def test_add_database_calls_enable_database():
    session = FakeSession({"enable_database": {"status": "enabled"}})
    run(make_adapter(session).add_database("p1"))
    assert session.calls == [("enable_database", {"project_id": "p1"})]


def test_publish_calls_deploy_project_and_returns_the_live_url():
    session = FakeSession({"deploy_project": {"url": "https://demo.lovable.app"}})
    url = run(make_adapter(session).publish("p1"))
    assert session.calls == [("deploy_project", {"project_id": "p1"})]
    assert url == "https://demo.lovable.app"


def test_publish_passes_the_slug_when_given():
    session = FakeSession({"deploy_project": {"url": "https://mi-barberia.lovable.app"}})
    run(make_adapter(session).publish("p1", name="mi-barberia"))
    assert session.calls[0][1] == {"project_id": "p1", "name": "mi-barberia"}


def test_publish_without_a_url_is_an_error():
    with pytest.raises(lovable.LovableError):
        run(make_adapter(FakeSession({"deploy_project": {}})).publish("p1"))


def test_change_sends_the_message_then_publishes_and_reports_credits():
    session = FakeSession(
        {
            "send_message": {"agent_response": {"status": "completed"}, "cost_credits": 0.7},
            "deploy_project": {"url": "https://demo.lovable.app"},
        }
    )
    result = run(make_adapter(session).change("p1", PROMPT))
    assert [name for name, _ in session.calls] == ["send_message", "deploy_project"]
    assert session.calls[0][1]["project_id"] == "p1"
    assert session.calls[0][1]["message"] == PROMPT
    assert session.calls[0][1]["wait"] is True
    assert result.credits == 0.7
    assert result.url == "https://demo.lovable.app"


def test_change_awaiting_input_raises_and_does_not_publish():
    session = FakeSession({"send_message": fixture("awaiting_input")})
    with pytest.raises(lovable.LovableNeedsInput):
        run(make_adapter(session).change("p1", "x"))
    assert [name for name, _ in session.calls] == ["send_message"]


def test_unpublish_sets_the_project_private_because_no_unpublish_tool_exists():
    session = FakeSession({"set_project_visibility": {}})
    run(make_adapter(session).unpublish("p1"))
    assert session.calls == [("set_project_visibility", {"project_id": "p1", "visibility": "private"})]


def test_recorded_build_is_labeled_demo_data():
    build = lovable.recorded_build()
    assert build.demo_data is True
    assert build.credits == 2.2


def test_no_log_line_contains_the_prompt_or_the_token(caplog):
    caplog.set_level(logging.DEBUG)
    session = FakeSession(
        {
            "create_project": fixture("create_project"),
            "enable_database": {},
            "deploy_project": {"url": "https://demo.lovable.app"},
            "send_message": {"agent_response": {"status": "completed"}, "cost_credits": 1},
            "set_project_visibility": {},
        }
    )
    adapter = make_adapter(session)
    run(adapter.build(PROMPT))
    run(adapter.add_database("p1"))
    run(adapter.publish("p1"))
    run(adapter.change("p1", PROMPT))
    run(adapter.unpublish("p1"))
    with pytest.raises(lovable.LovableNeedsInput):
        run(make_adapter(FakeSession({"create_project": fixture("awaiting_input")})).build(PROMPT))
    assert caplog.records, "the adapter should log its steps"
    assert PROMPT not in caplog.text
    assert "SECRET" not in caplog.text
    assert TOKEN not in caplog.text
