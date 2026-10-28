"""Linear service: epics (parent issues) and issues with acceptance criteria, idempotent."""
from __future__ import annotations

import json
import time
from collections.abc import Iterator
from pathlib import Path

import httpx

from app.config import settings
from app.schemas.content import BacklogItem
from app.schemas.run import EventType, StageEvent

LINEAR_URL = "https://api.linear.app/graphql"
FIXTURES = Path(__file__).resolve().parent.parent / "fixtures" / "linear"
BACKLOG_STAGE = 6
MARKER = "external_id:"

FIND_ISSUE = """
query FindIssue($teamId: ID!, $marker: String!) {
  issues(first: 1, filter: {team: {id: {eq: $teamId}}, description: {contains: $marker}}) {
    nodes { id identifier url }
  }
}
"""

CREATE_ISSUE = """
mutation IssueCreate($input: IssueCreateInput!) {
  issueCreate(input: $input) {
    success
    issue { id identifier url }
  }
}
"""


class LinearError(RuntimeError):
    pass


def _marker(external_id: str) -> str:
    return f"{MARKER} {external_id}"


def _description(acceptance: list[str], external_id: str) -> str:
    criteria = "\n".join(f"- [ ] {c}" for c in acceptance)
    body = f"## Acceptance criteria\n{criteria}\n\n" if criteria else ""
    return f"{body}{_marker(external_id)}"


class LinearClient:
    def __init__(self, api_key: str, team_id: str, client: httpx.Client | None = None):
        self.team_id = team_id
        self._http = client or httpx.Client(timeout=20)
        self._headers = {"Authorization": api_key, "Content-Type": "application/json"}

    def _gql(self, query: str, variables: dict) -> dict:
        resp = self._http.post(
            LINEAR_URL, headers=self._headers, json={"query": query, "variables": variables}
        )
        resp.raise_for_status()
        body = resp.json()
        if body.get("errors"):
            raise LinearError(body["errors"][0].get("message", "unknown Linear error"))
        return body["data"]

    def find(self, external_id: str) -> dict | None:
        data = self._gql(
            FIND_ISSUE, {"teamId": self.team_id, "marker": _marker(external_id)}
        )
        nodes = data["issues"]["nodes"]
        return nodes[0] if nodes else None

    def ensure_issue(
        self,
        title: str,
        external_id: str,
        acceptance: list[str],
        parent_id: str | None = None,
    ) -> dict:
        """Return the existing issue carrying `external_id`, or create it."""
        existing = self.find(external_id)
        if existing:
            return existing
        issue_input = {
            "teamId": self.team_id,
            "title": title,
            "description": _description(acceptance, external_id),
        }
        if parent_id:
            issue_input["parentId"] = parent_id
        data = self._gql(CREATE_ISSUE, {"input": issue_input})["issueCreate"]
        if not data.get("success"):
            raise LinearError(f"issueCreate failed for {external_id}")
        return data["issue"]


def _demo_issues() -> list[dict]:
    return json.loads((FIXTURES / "demo_backlog.json").read_text(encoding="utf-8"))


def _event(run_id: str, item: BacklogItem, t0: float, demo: bool) -> StageEvent:
    return StageEvent(
        run_id=run_id,
        stage=BACKLOG_STAGE,
        type=EventType.linear_issue,
        payload=item.model_dump(mode="json"),
        ts=round(time.monotonic() - t0, 3),
        demo_data=demo,
    )


def create_backlog(
    items: list[BacklogItem],
    run_id: str,
    client: LinearClient | None = None,
) -> Iterator[StageEvent]:
    """Create one epic per distinct `item.epic` plus one issue per item; yield one
    `linear_issue` event per issue. Safe to re-run: the `external_id` marker in each
    description makes an existing issue be reused instead of duplicated."""
    t0 = time.monotonic()

    if settings.DEMO_MODE:
        recorded = _demo_issues()
        if len(items) > len(recorded):
            raise LinearError(f"demo fixture has {len(recorded)} issues, got {len(items)}")
        for item, rec in zip(items, recorded):
            replayed = item.model_copy(
                update={
                    "linear_id": rec["identifier"],
                    "url": rec["url"],
                    "demo_data": True,
                }
            )
            yield _event(run_id, replayed, t0, demo=True)
        return

    if client is None:
        if not (settings.LINEAR_API_KEY and settings.LINEAR_TEAM_ID):
            raise LinearError("LINEAR_API_KEY and LINEAR_TEAM_ID are required when DEMO_MODE=0")
        client = LinearClient(settings.LINEAR_API_KEY, settings.LINEAR_TEAM_ID)

    epic_ids: dict[str, str] = {}
    for item in items:
        if item.epic not in epic_ids:
            epic = client.ensure_issue(
                title=f"Epic: {item.epic}",
                external_id=f"epic:{item.epic}",
                acceptance=[],
            )
            epic_ids[item.epic] = epic["id"]
        issue = client.ensure_issue(
            title=item.title,
            external_id=item.external_id,
            acceptance=item.acceptance,
            parent_id=epic_ids[item.epic],
        )
        done = item.model_copy(
            update={"linear_id": issue["identifier"], "url": issue["url"]}
        )
        yield _event(run_id, done, t0, demo=False)
