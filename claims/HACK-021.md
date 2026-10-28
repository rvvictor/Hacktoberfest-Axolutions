# HACK-021
ID: HACK-021
State: CLAIMED
Owner: victor-2
Branch: feat/hack-021
Worktree: /Users/victor/Documents/Proyectos/Hacktoberfest-Axolutions-wt/hack-021
Worklog: worklog/WL-1793165106-victor-2-HACK-021-hack.0IPJIw.md
Priority: P1
Paths: app/routers/hunter.py, app/fixtures/hunter/, app/tests/test_hunter.py, web/src/features/hunter/
Depends: HACK-003
Verify: `uv run pytest -q app/tests/test_hunter.py && npm --prefix web run build && bash .uak/bin/design-lint`
Lease-Until: 1793167806
Updated: 1793165106
Task-Base: 9c7e27306e7a6412169c009d2071e439c03c4c42
Next: write the prospects fixture and the router on the `outreach.py` contract.
PR: -
Evidence: -
