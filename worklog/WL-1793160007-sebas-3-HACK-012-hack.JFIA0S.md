# worklog/WL-1793160007-sebas-3-HACK-012-hack.JFIA0S.md · HACK-012

## Live summary
- Done: RLS check (quality/check_rls.py, stdlib) on supabase/migrations; quality.run(repo) -> QualityReport (rls in-process); CI template quality/generated-repo-ci.yml (build, lint, gitleaks, npm audit, rls, smoke); good/bad fixtures (demo_data: true); 8 tests green
- Decision: CI-only checks (build, lint, gitleaks, npm audit, smoke) are named in report.details, not reported as passed; QualityCheck has no 'skipped' state
- Why: run() cannot build or scan a generated repo in-process without installing its deps; a passed=True for unrun checks would be a false green (IDEA.md §5 honest validation)
- Failing: none in final run; earlier: ruff flagged regex flag and parens (fixed)
- Commands: bash .uak/bin/q uv run pytest -q app/tests/test_quality.py -> OK exit=0 (7 passed); bash .uak/bin/q uv run pytest -q -> OK exit=0 (12 passed)
- Next: wait for HACK-001 and HACK-002 INTEGRATED; then open PR and uak done HACK-012. Smoke step needs a generated playwright.config with @smoke tag

## History
- 1793160007 | CLAIMED | sebas-3 | claim; next: write `check_rls.py` against `app/fixtures/quality/bad/supabase/migrations/`.
- 1793160123 | CLAIMED | sebas-3 | checkpoint; next: wait for HACK-001 and HACK-002 INTEGRATED; then open PR and uak done HACK-012. Smoke step needs a generated playwright.config with @smoke tag
- 1793160246 | AVAILABLE | sebas-3 | release; claim released by sebas-3; reason: -; summary kept
- 1793160298 | CLAIMED | jabi-2 | claim; next: wait for HACK-001 and HACK-002 INTEGRATED; then open PR and uak done HACK-012. Smoke step needs a generated playwright.config with @smoke tag
