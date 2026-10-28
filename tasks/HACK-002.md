# HACK-002
ID: HACK-002
State: REVIEW
Owner: victor-2
Branch: feat/hack-002
Worktree: /Users/victor/Documents/Proyectos/Hacktoberfest-Axolutions-wt/hack-002
Worklog: worklog/WL-1793158422-victor-2-HACK-002-hack.yufxo6.md
Priority: P0
Paths: app/schemas/, app/fixtures/demo/, app/tests/test_schemas.py, web/src/lib/types.ts, web/src/lib/mock.ts
Depends: None
Verify: `uv run pytest -q app/tests/test_schemas.py`
Lease-Until: 1793174617
Updated: 1793160217
Task-Base: 3eaff8c29896351940d265a98a095de33a6e5cb7
Next: Humano: Smoke red or product unverified: PRODUCT_FAIL: adapter exit=1 (log: /Users/victor/Documents/Proyectos/Hacktoberfest-Axolutions/.git/uak-out/gate-HACK-002-smoke-1793163805.log)
PR: https://github.com/rvvictor/Hacktoberfest-Axolutions/pull/1
Evidence: pytest test_schemas via uv --no-project (pydantic,pytest) exit 0, 4 passed; literal Verify blocked until HACK-001 pyproject; smoke unavailable
Events: 10
Checkpoints: 1
Sessions: 6
Last-Checkpoint: 1793158535
Progress: 1 commit(s) since the claim · last: 82fa2e9 feat(HACK-002): schemas, demo run fixture, TS types and replay (29 minutes ago) · 0 uncommitted tracked file(s) · at 1793160217
Progress-Head: 82fa2e9/4294967295
Progress-Changed: 1793159100
Task-Tip: 82fa2e963c54385720f5dcb8fd3daaa9ac9bbafd
