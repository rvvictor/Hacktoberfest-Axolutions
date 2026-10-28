"""Quality gate for a generated repo: returns a QualityReport with each check's status.

In-process checks: rls. The rest (build, lint, gitleaks, npm audit, smoke) run in the
generated repo's CI from quality/generated-repo-ci.yml, so they are named in `details`
instead of being reported as passed.
"""

from __future__ import annotations

from pathlib import Path

from app.schemas.content import QualityCheck, QualityReport
from quality.check_rls import check_rls

CI_ONLY_CHECKS = "build, lint, gitleaks, npm audit, smoke: not run here, see quality/generated-repo-ci.yml"


def run(repo_path: str | Path, *, demo_data: bool = False) -> QualityReport:
    rls = check_rls(repo_path)
    checks = [QualityCheck(name="rls", passed=rls.passed, details=rls.details)]
    return QualityReport(
        checks=checks,
        passed=all(c.passed for c in checks),
        details=CI_ONLY_CHECKS,
        demo_data=demo_data,
    )
