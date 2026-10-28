"""Quality gate tests. Fixtures under app/fixtures/quality are synthetic (demo_data: true)."""

import subprocess
import sys
from pathlib import Path

from app.services import quality
from quality.check_rls import check_sql

ROOT = Path(__file__).resolve().parents[2]
FIXTURES = ROOT / "app" / "fixtures" / "quality"
GOOD = FIXTURES / "good"
BAD = FIXTURES / "bad"


def test_good_repo_passes_rls() -> None:
    report = quality.run(GOOD, demo_data=True)
    assert report.passed is True
    assert report.demo_data is True
    assert [(c.name, c.passed) for c in report.checks] == [("rls", True)]


def test_bad_repo_fails_rls_with_table_names() -> None:
    report = quality.run(BAD, demo_data=True)
    assert report.passed is False
    rls = report.checks[0]
    assert (rls.name, rls.passed) == ("rls", False)
    assert "profiles: row level security not enabled" in rls.details
    assert "projects: only trivial policies" in rls.details


def test_ci_only_checks_are_named_not_passed() -> None:
    report = quality.run(GOOD)
    assert "npm audit" in report.details and "smoke" in report.details
    assert {c.name for c in report.checks} == {"rls"}


def test_rls_rule_cases() -> None:
    enabled = "create table t (id int); alter table t enable row level security;"
    # Real policy: passes.
    assert check_sql(
        [enabled + "create policy p on t for select using (auth.uid() = id);"]
    ).passed
    # Only `using (true)`, with or without `with check (true)`: fails.
    assert not check_sql(
        [enabled + "create policy p on t for all using (true) with check (true);"]
    ).passed
    # One trivial policy next to a real one: passes (the real one restricts rows).
    assert check_sql(
        [
            enabled
            + "create policy a on t for all using (true); create policy b on t for select using (id = 1);"
        ]
    ).passed
    # RLS disabled again later in the history: fails.
    assert not check_sql([enabled + "alter table t disable row level security;"]).passed
    # Comments and a quoted policy name with " on " do not confuse the parser.
    assert check_sql(
        "-- create table x (id int);\ncreate table t (id int); alter table t enable row level security;"
        ' create policy "read on own rows" on t for select using (auth.uid() = id);'
    ).passed


def test_repo_without_migrations_passes_with_note(tmp_path: Path) -> None:
    result = quality.run(tmp_path)
    assert result.passed is True
    assert "nothing to check" in result.checks[0].details


def test_check_rls_cli_exit_codes() -> None:
    script = str(ROOT / "quality" / "check_rls.py")
    ok = subprocess.run(
        [sys.executable, "-I", script, str(GOOD)],
        capture_output=True,
        text=True,
        check=False,
    )
    bad = subprocess.run(
        [sys.executable, "-I", script, str(BAD)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert ok.returncode == 0 and ok.stdout.startswith("PASS rls")
    assert bad.returncode == 1 and bad.stdout.startswith("FAIL rls")


def test_ci_template_covers_all_gates() -> None:
    text = (ROOT / "quality" / "generated-repo-ci.yml").read_text(encoding="utf-8")
    for needle in (
        "npm run build",
        "npm run lint",
        "gitleaks",
        "npm audit",
        "check_rls.py",
        "playwright",
    ):
        assert needle in text, needle
