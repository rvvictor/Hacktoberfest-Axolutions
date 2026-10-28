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
Lease-Until: 1793179667
Updated: 1793165267
Task-Base: 9c7e27306e7a6412169c009d2071e439c03c4c42
Next: Another agent reviews https://github.com/rvvictor/Hacktoberfest-Axolutions/pull/15; run .uak/bin/smoke
PR: https://github.com/rvvictor/Hacktoberfest-Axolutions/pull/15
Evidence: pytest test_hunter+test_outreach exit 0; web build + design-lint pass; smoke PRODUCT_PASS; criteria: prospects demo_data, draft→approved→sent→replied, rules panel
Events: 3
Checkpoints: 0
Sessions: 1
Last-Checkpoint: 0
Progress: 0 commit(s) since the claim · last: 9c7e273 Merge pull request #7 from rvvictor/feat/hack-012 (5 minutes ago) · 0 uncommitted tracked file(s) · at 1793165125
Progress-Head: 9c7e273/4294967295
Progress-Changed: 1793165125
Task-Tip: 1e10e9ee8125dc3132da2d66c385b60d3188f959
