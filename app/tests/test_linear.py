import json

import httpx
import pytest
import respx

from app.config import settings
from app.schemas.content import BacklogItem
from app.schemas.run import EventType
from app.services import linear
from app.services.linear import LinearClient, LinearError, create_backlog


def _items(n: int = 6) -> list[BacklogItem]:
    return [
        BacklogItem(
            epic="Auth" if i < 3 else "Gastos",
            title=f"Issue {i}",
            acceptance=[f"Criterio {i}"],
            external_id=f"ext-{i}",
        )
        for i in range(n)
    ]


class FakeLinear:
    """Stateful stand-in for api.linear.app/graphql."""

    def __init__(self):
        self.issues: list[dict] = []
        self.creates = 0

    def __call__(self, request: httpx.Request) -> httpx.Response:
        body = json.loads(request.content)
        v = body["variables"]
        if "issueCreate" in body["query"]:
            self.creates += 1
            n = len(self.issues) + 1
            issue = {
                "id": f"id-{n}",
                "identifier": f"SPD-{n}",
                "url": f"https://linear.app/t/issue/SPD-{n}",
                "description": v["input"]["description"],
                "parentId": v["input"].get("parentId"),
                "title": v["input"]["title"],
            }
            self.issues.append(issue)
            return httpx.Response(
                200, json={"data": {"issueCreate": {"success": True, "issue": issue}}}
            )
        nodes = [i for i in self.issues if v["marker"] in i["description"]][:1]
        return httpx.Response(200, json={"data": {"issues": {"nodes": nodes}}})


@pytest.fixture
def live(monkeypatch):
    monkeypatch.setattr(settings, "DEMO_MODE", False)
    fake = FakeLinear()
    with respx.mock:
        respx.post(linear.LINEAR_URL).mock(side_effect=fake)
        yield fake, LinearClient("key", "team-1")


def test_creates_one_event_per_issue_with_identifier_and_url(live):
    _, client = live
    events = list(create_backlog(_items(6), "run1", client))
    assert len(events) == 6
    assert all(e.type == EventType.linear_issue and e.stage == 6 for e in events)
    assert events[0].payload["linear_id"] == "SPD-2"  # SPD-1 is the Auth epic
    assert events[0].payload["url"].startswith("https://linear.app/")
    assert all(not e.demo_data for e in events)
    assert [e.ts for e in events] == sorted(e.ts for e in events)


def test_epics_become_parent_issues_and_criteria_are_in_description(live):
    fake, client = live
    list(create_backlog(_items(6), "run1", client))
    epics = [i for i in fake.issues if i["title"].startswith("Epic: ")]
    assert [e["title"] for e in epics] == ["Epic: Auth", "Epic: Gastos"]
    children = [i for i in fake.issues if i["parentId"]]
    assert len(children) == 6
    assert "- [ ] Criterio 0" in children[0]["description"]
    assert "external_id: ext-0" in children[0]["description"]


def test_rerun_is_idempotent(live):
    fake, client = live
    first = list(create_backlog(_items(6), "run1", client))
    created = fake.creates
    second = list(create_backlog(_items(6), "run1", client))
    assert fake.creates == created  # nothing new created
    assert len(fake.issues) == 8  # 2 epics + 6 issues
    assert [e.payload["linear_id"] for e in second] == [e.payload["linear_id"] for e in first]


def test_graphql_error_raises(live):
    _, client = live
    respx.post(linear.LINEAR_URL).mock(
        return_value=httpx.Response(200, json={"errors": [{"message": "bad team"}]})
    )
    with pytest.raises(LinearError, match="bad team"):
        list(create_backlog(_items(1), "run1", client))


def test_live_without_credentials_fails_clearly(monkeypatch):
    monkeypatch.setattr(settings, "DEMO_MODE", False)
    monkeypatch.setattr(settings, "LINEAR_API_KEY", None)
    with pytest.raises(LinearError, match="LINEAR_API_KEY"):
        list(create_backlog(_items(1), "run1"))


def test_demo_mode_replays_recorded_issues_without_network(monkeypatch):
    monkeypatch.setattr(settings, "DEMO_MODE", True)
    with respx.mock:  # any real request would raise: no routes registered
        events = list(create_backlog(_items(6), "run1"))
    assert len(events) == 6
    assert all(e.demo_data and e.payload["demo_data"] for e in events)
    assert events[0].payload["linear_id"] == "SPD-1"
    assert events[0].payload["external_id"] == "ext-0"
    assert events[0].payload["title"] == "Issue 0"


def test_demo_mode_rejects_more_items_than_recorded(monkeypatch):
    monkeypatch.setattr(settings, "DEMO_MODE", True)
    with pytest.raises(LinearError):
        list(create_backlog(_items(9), "run1"))
