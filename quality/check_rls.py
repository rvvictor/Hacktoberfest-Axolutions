"""Fails when a Supabase table has no row level security, or only trivial policies.

Stdlib only, so the CI template can run it without installing the app:
    python quality/check_rls.py PATH_TO_REPO      (exit 0 = pass, 1 = fail)
The app imports check_rls() from services/quality.py.
"""

from __future__ import annotations

import re
import sys
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class RlsResult:
    passed: bool
    tables: list[str] = field(default_factory=list)
    problems: list[str] = field(default_factory=list)
    note: str = ""

    @property
    def details(self) -> str:
        if self.problems:
            return "; ".join(self.problems)
        return self.note or f"{len(self.tables)} table(s) protected by RLS"


def _strip_comments(sql: str) -> str:
    sql = re.sub(r"/\*.*?\*/", " ", sql, flags=re.DOTALL)
    return re.sub(r"--[^\n]*", " ", sql)


def _clauses(stmt: str) -> list[str]:
    """Contents of every `using (...)` and `with check (...)` clause, parentheses balanced."""
    out: list[str] = []
    for m in re.finditer(r"\b(?:using|with\s+check)\s*\(", stmt):
        depth, j = 1, m.end()
        while j < len(stmt) and depth:
            depth += {"(": 1, ")": -1}.get(stmt[j], 0)
            j += 1
        out.append(" ".join(stmt[m.end() : j - 1].split()))
    return out


def _is_trivial(clauses: list[str]) -> bool:
    # No clause at all, or only `true`, lets every row through.
    return all(c.strip("() ") == "true" for c in clauses)


_IDENT = r'(?:"?public"?\.)?"?(\w+)"?'


def check_sql(migrations: list[str]) -> RlsResult:
    """Check migrations in order; each item is the full text of one .sql file."""
    rls: dict[str, bool] = {}
    policies: dict[str, list[bool]] = {}  # table -> one trivial? flag per policy

    for sql in migrations:
        for raw in _strip_comments(sql).split(";"):
            s = " ".join(raw.split()).lower()
            if not s:
                continue
            if m := re.match(rf"create table (?:if not exists )?(?:only )?{_IDENT}", s):
                rls.setdefault(m.group(1), False)
            elif m := re.match(
                rf"alter table (?:if exists )?(?:only )?{_IDENT} enable row level security",
                s,
            ):
                rls[m.group(1)] = True
            elif m := re.match(
                rf"alter table (?:if exists )?(?:only )?{_IDENT} disable row level security",
                s,
            ):
                rls[m.group(1)] = False
            elif m := re.match(rf'create policy (?:"[^"]*"|\S+) on {_IDENT}', s):
                policies.setdefault(m.group(1), []).append(_is_trivial(_clauses(s)))

    problems: list[str] = []
    for table in sorted(set(rls) | set(policies)):
        if not rls.get(table, False):
            problems.append(f"{table}: row level security not enabled")
        elif policies.get(table) and all(policies[table]):
            problems.append(f"{table}: only trivial policies (using (true))")

    note = ""
    if not problems and any(rls.get(t) and not policies.get(t) for t in rls):
        note = "RLS enabled with no policies (deny-all for non-owner roles)"
    return RlsResult(
        passed=not problems,
        tables=sorted(rls),
        problems=problems,
        note=note,
    )


def check_rls(repo_path: str | Path) -> RlsResult:
    migrations_dir = Path(repo_path) / "supabase" / "migrations"
    if not migrations_dir.is_dir():
        return RlsResult(
            passed=True, note="no supabase/migrations found: nothing to check"
        )
    files = sorted(migrations_dir.glob("*.sql"))
    return check_sql([f.read_text(encoding="utf-8") for f in files])


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print("usage: python quality/check_rls.py PATH_TO_REPO", file=sys.stderr)
        return 2
    result = check_rls(argv[1])
    print(("PASS" if result.passed else "FAIL") + " rls: " + result.details)
    return 0 if result.passed else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
