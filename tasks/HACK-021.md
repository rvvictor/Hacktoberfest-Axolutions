# HACK-021
ID: HACK-021
State: REVIEW
Owner: victor-2
Branch: feat/hack-021
Worktree: /Users/victor/Documents/Proyectos/Hacktoberfest-Axolutions-wt/hack-021
Worklog: worklog/WL-1793165106-victor-2-HACK-021-hack.0IPJIw.md
Priority: P1
Paths: app/routers/hunter.py, app/fixtures/hunter/, app/tests/test_hunter.py, web/src/features/hunter/
Depends: HACK-003
Verify: `uv run pytest -q app/tests/test_hunter.py && npm --prefix web run build && bash .uak/bin/design-lint`
Lease-Until: 1793179943
Updated: 1793165543
Task-Base: 9c7e27306e7a6412169c009d2071e439c03c4c42
Next: Wait for review of SHA 1e10e9e
PR: https://github.com/rvvictor/Hacktoberfest-Axolutions/pull/15
Evidence: pytest test_hunter+test_outreach exit 0; web build + design-lint pass; smoke PRODUCT_PASS; criteria: prospects demo_data, draft→approved→sent→replied, rules panel
Events: 6
Checkpoints: 1
Sessions: 3
Last-Checkpoint: 1793165271
Progress: 4 commit(s) since the claim · last: 1e10e9e feat(HACK-021): hunter console API and UI with human-approved outreach (5 minutes ago) · 0 uncommitted tracked file(s) · at 1793165543
Progress-Head: 1e10e9e/4294967295
Progress-Changed: 1793165543
Task-Tip: 1e10e9ee8125dc3132da2d66c385b60d3188f959
