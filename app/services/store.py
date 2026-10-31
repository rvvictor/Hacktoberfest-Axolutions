"""SQLite store for runs (IDEA.md §5): the versioned spec is the source of truth.

One connection per call: SQLite serialises writers and FastAPI runs sync code in a threadpool.
"""
from __future__ import annotations

import json
import sqlite3
import time
import uuid
from contextlib import closing
from typing import Any

from app.config import settings
from app.schemas import Approval, Mode, Project, Run, RunStatus, StageEvent

SCHEMA = """
CREATE TABLE IF NOT EXISTS projects (
    id TEXT PRIMARY KEY, mode TEXT NOT NULL, idea TEXT NOT NULL,
    stack_prefs TEXT NOT NULL, demo_data INTEGER NOT NULL DEFAULT 0
);
CREATE TABLE IF NOT EXISTS runs (
    run_id TEXT PRIMARY KEY, project_id TEXT NOT NULL, stage INTEGER NOT NULL,
    status TEXT NOT NULL, awaiting TEXT, approvals TEXT NOT NULL,
    demo_data INTEGER NOT NULL DEFAULT 0, created REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS events (
    seq INTEGER PRIMARY KEY AUTOINCREMENT, run_id TEXT NOT NULL, event TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS events_run ON events (run_id, seq);
CREATE TABLE IF NOT EXISTS specs (
    run_id TEXT NOT NULL, version INTEGER NOT NULL, spec TEXT NOT NULL,
    PRIMARY KEY (run_id, version)
);
CREATE TABLE IF NOT EXISTS external_ids (
    run_id TEXT NOT NULL, stage INTEGER NOT NULL, key TEXT NOT NULL, value TEXT NOT NULL,
    PRIMARY KEY (run_id, stage, key)
);
CREATE TABLE IF NOT EXISTS costs (
    run_id TEXT NOT NULL, step TEXT NOT NULL, usd REAL NOT NULL DEFAULT 0,
    PRIMARY KEY (run_id, step)
);
CREATE TABLE IF NOT EXISTS answers (
    run_id TEXT NOT NULL, seq INTEGER NOT NULL, answer TEXT NOT NULL,
    PRIMARY KEY (run_id, seq)
);
CREATE TABLE IF NOT EXISTS users (
    id TEXT PRIMARY KEY, google_sub TEXT NOT NULL UNIQUE, email TEXT NOT NULL, created REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS sessions (
    token_sha256 TEXT PRIMARY KEY, user_id TEXT NOT NULL, expires REAL NOT NULL
);
"""
# Columns added after the first release (expand step): SQLite has no ADD COLUMN IF NOT EXISTS.
LATER_COLUMNS = {"projects": {"owner_id": "TEXT", "created": "REAL"}}


def _connect() -> sqlite3.Connection:
    settings.DATA_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(settings.DATA_DIR / "speedhack.db", timeout=10)
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA)
    for table, columns in LATER_COLUMNS.items():
        have = {row["name"] for row in conn.execute(f"PRAGMA table_info({table})")}
        for name, kind in columns.items():
            if name not in have:
                conn.execute(f"ALTER TABLE {table} ADD COLUMN {name} {kind}")
    return conn


def _run_from_row(conn: sqlite3.Connection, row: sqlite3.Row) -> Run:
    costs = {r["step"]: r["usd"] for r in conn.execute("SELECT * FROM costs WHERE run_id=?", (row["run_id"],))}
    return Run(
        run_id=row["run_id"],
        project_id=row["project_id"],
        stage=row["stage"],
        status=RunStatus(row["status"]),
        approvals=[Approval(**a) for a in json.loads(row["approvals"])],
        cost_by_step=costs,
        demo_data=bool(row["demo_data"]),
    )


def create_run(mode: Mode, idea: str, stack_prefs: list[str], demo_data: bool) -> tuple[Project, Run]:
    project = Project(id=f"prj_{uuid.uuid4().hex[:8]}", mode=mode, idea=idea, stack_prefs=stack_prefs, demo_data=demo_data)
    run_id = f"run_{uuid.uuid4().hex[:8]}"
    approvals = [Approval(number=n).model_dump(mode="json") for n in (1, 2, 3)]
    with closing(_connect()) as conn, conn:
        conn.execute(
            "INSERT INTO projects (id, mode, idea, stack_prefs, demo_data, created) VALUES (?,?,?,?,?,?)",
            (project.id, mode.value, idea, json.dumps(stack_prefs), int(demo_data), time.time()),
        )
        conn.execute(
            "INSERT INTO runs (run_id, project_id, stage, status, awaiting, approvals, demo_data, created)"
            " VALUES (?,?,?,?,?,?,?,?)",
            (run_id, project.id, 1, RunStatus.pending.value, "start", json.dumps(approvals), int(demo_data), time.time()),
        )
    return project, get_run(run_id)  # type: ignore[return-value]


def get_run(run_id: str) -> Run | None:
    with closing(_connect()) as conn:
        row = conn.execute("SELECT * FROM runs WHERE run_id=?", (run_id,)).fetchone()
        return _run_from_row(conn, row) if row else None


def get_project(project_id: str) -> Project:
    with closing(_connect()) as conn:
        row = conn.execute("SELECT * FROM projects WHERE id=?", (project_id,)).fetchone()
    return Project(
        id=row["id"], mode=Mode(row["mode"]), idea=row["idea"],
        stack_prefs=json.loads(row["stack_prefs"]), demo_data=bool(row["demo_data"]),
    )


def get_awaiting(run_id: str) -> str | None:
    """What the run waits for: "start", "answers", "approval:N", or None while running/done."""
    with closing(_connect()) as conn:
        row = conn.execute("SELECT awaiting FROM runs WHERE run_id=?", (run_id,)).fetchone()
    return row["awaiting"] if row else None


def claim(run_id: str, expected: str) -> bool:
    """Atomically take the run out of `expected`. Only one caller wins, so a stage never runs twice."""
    with closing(_connect()) as conn, conn:
        cur = conn.execute(
            "UPDATE runs SET awaiting=NULL, status=? WHERE run_id=? AND awaiting=?",
            (RunStatus.running.value, run_id, expected),
        )
        return cur.rowcount == 1


def set_state(
    run_id: str,
    *,
    stage: int | None = None,
    status: RunStatus | None = None,
    awaiting: str | None = None,
    approvals: list[Approval] | None = None,
) -> None:
    """Update stage/status/approvals; `awaiting` is always written (None clears it)."""
    sets, args = ["awaiting=?"], [awaiting]
    if stage is not None:
        sets.append("stage=?")
        args.append(stage)
    if status is not None:
        sets.append("status=?")
        args.append(status.value)
    if approvals is not None:
        sets.append("approvals=?")
        args.append(json.dumps([a.model_dump(mode="json") for a in approvals]))
    with closing(_connect()) as conn, conn:
        conn.execute(f"UPDATE runs SET {', '.join(sets)} WHERE run_id=?", (*args, run_id))


def elapsed(run_id: str) -> float:
    with closing(_connect()) as conn:
        row = conn.execute("SELECT created FROM runs WHERE run_id=?", (run_id,)).fetchone()
    return max(0.0, time.time() - row["created"])


def add_event(event: StageEvent) -> int:
    with closing(_connect()) as conn, conn:
        cur = conn.execute(
            "INSERT INTO events (run_id, event) VALUES (?,?)", (event.run_id, event.model_dump_json())
        )
        return int(cur.lastrowid)


def list_events(run_id: str, after: int = 0) -> list[tuple[int, StageEvent]]:
    with closing(_connect()) as conn:
        rows = conn.execute(
            "SELECT seq, event FROM events WHERE run_id=? AND seq>? ORDER BY seq", (run_id, after)
        ).fetchall()
    return [(r["seq"], StageEvent.model_validate_json(r["event"])) for r in rows]


def add_spec(run_id: str, spec: dict[str, Any]) -> int:
    """Store `spec` as the next version and return that version number."""
    with closing(_connect()) as conn, conn:
        row = conn.execute("SELECT COALESCE(MAX(version), 0) AS v FROM specs WHERE run_id=?", (run_id,)).fetchone()
        version = row["v"] + 1
        conn.execute(
            "INSERT INTO specs VALUES (?,?,?)", (run_id, version, json.dumps({**spec, "version": version}))
        )
    return version


def get_spec(run_id: str, version: int | None = None) -> dict[str, Any] | None:
    query, args = "SELECT spec FROM specs WHERE run_id=?", [run_id]
    if version is not None:
        query += " AND version=?"
        args.append(version)
    with closing(_connect()) as conn:
        row = conn.execute(query + " ORDER BY version DESC LIMIT 1", args).fetchone()
    return json.loads(row["spec"]) if row else None


def set_external(run_id: str, stage: int, key: str, value: str) -> None:
    with closing(_connect()) as conn, conn:
        conn.execute("INSERT OR REPLACE INTO external_ids VALUES (?,?,?,?)", (run_id, stage, key, value))


def get_externals(run_id: str, stage: int) -> dict[str, str]:
    with closing(_connect()) as conn:
        rows = conn.execute("SELECT key, value FROM external_ids WHERE run_id=? AND stage=?", (run_id, stage))
        return {r["key"]: r["value"] for r in rows}


def add_cost(run_id: str, step: str, usd: float) -> None:
    with closing(_connect()) as conn, conn:
        conn.execute(
            "INSERT INTO costs VALUES (?,?,?) ON CONFLICT(run_id, step) DO UPDATE SET usd = usd + excluded.usd",
            (run_id, step, usd),
        )


def add_answers(run_id: str, answers: list[str]) -> None:
    with closing(_connect()) as conn, conn:
        base = conn.execute("SELECT COALESCE(MAX(seq), 0) AS s FROM answers WHERE run_id=?", (run_id,)).fetchone()["s"]
        conn.executemany(
            "INSERT INTO answers VALUES (?,?,?)", [(run_id, base + i + 1, a) for i, a in enumerate(answers)]
        )


def get_answers(run_id: str) -> list[str]:
    with closing(_connect()) as conn:
        rows = conn.execute("SELECT answer FROM answers WHERE run_id=? ORDER BY seq", (run_id,)).fetchall()
    return [r["answer"] for r in rows]


def mark_demo(run_id: str) -> None:
    """A stage fell back to recorded data, so the whole run is labeled demo_data."""
    with closing(_connect()) as conn, conn:
        conn.execute("UPDATE runs SET demo_data=1 WHERE run_id=?", (run_id,))


# --- accounts (spec 001) ----------------------------------------------------------------------


def upsert_user(google_sub: str, email: str) -> str:
    """The user id for this Google account, created on the first sign-in; the email follows Google's."""
    with closing(_connect()) as conn, conn:
        row = conn.execute("SELECT id FROM users WHERE google_sub=?", (google_sub,)).fetchone()
        if row:
            conn.execute("UPDATE users SET email=? WHERE id=?", (email, row["id"]))
            return row["id"]
        user_id = f"usr_{uuid.uuid4().hex[:12]}"
        conn.execute("INSERT INTO users VALUES (?,?,?,?)", (user_id, google_sub, email, time.time()))
        return user_id


def add_session(token_sha256: str, user_id: str, expires: float) -> None:
    with closing(_connect()) as conn, conn:
        conn.execute("INSERT INTO sessions VALUES (?,?,?)", (token_sha256, user_id, expires))


def session_user(token_sha256: str, now: float) -> dict[str, Any] | None:
    """The signed-in user of an unexpired session; an expired row is deleted."""
    with closing(_connect()) as conn, conn:
        row = conn.execute(
            "SELECT s.expires, u.id, u.email FROM sessions s JOIN users u ON u.id = s.user_id WHERE s.token_sha256=?",
            (token_sha256,),
        ).fetchone()
        if row is None:
            return None
        if row["expires"] <= now:
            conn.execute("DELETE FROM sessions WHERE token_sha256=?", (token_sha256,))
            return None
        return {"id": row["id"], "email": row["email"]}


def delete_session(token_sha256: str) -> None:
    with closing(_connect()) as conn, conn:
        conn.execute("DELETE FROM sessions WHERE token_sha256=?", (token_sha256,))


def projects_since(owner_id: str, since: float) -> int:
    with closing(_connect()) as conn:
        return conn.execute(
            "SELECT COUNT(*) FROM projects WHERE owner_id=? AND created>=?", (owner_id, since)
        ).fetchone()[0]
