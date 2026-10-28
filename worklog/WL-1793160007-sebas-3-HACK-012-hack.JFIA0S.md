# worklog/WL-1793160007-sebas-3-HACK-012-hack.JFIA0S.md · HACK-012

## Live summary
- Done: Claim created; implementation pending
- Decision: Own branch and worktree
- Why: Parallel work without touching the main checkout
- Failing: No validation run yet
- Commands: `uv run pytest -q app/tests/test_quality.py`
- Next: write `check_rls.py` against `app/fixtures/quality/bad/supabase/migrations/`.

## History
- 1793160007 | CLAIMED | sebas-3 | claim; next: write `check_rls.py` against `app/fixtures/quality/bad/supabase/migrations/`.
