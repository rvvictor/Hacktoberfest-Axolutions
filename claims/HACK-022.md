# HACK-022
ID: HACK-022
State: CLAIMED
Owner: victor-2
Branch: feat/hack-022
Worktree: /Users/victor/Documents/Proyectos/Hacktoberfest-Axolutions-wt/hack-022
Worklog: worklog/WL-1793165521-victor-2-HACK-022-hack.uuIv5N.md
Priority: P2
Paths: app/routers/ops.py, app/services/costs.py, app/tests/test_ops.py, web/src/features/ops/
Depends: HACK-003
Verify: `uv run pytest -q app/tests/test_ops.py && npm --prefix web run build && bash .uak/bin/design-lint`
Lease-Until: 1793168236
Updated: 1793165536
Task-Base: 744a3d8d69b7811e0b40fd39d23007558149e1c7
Next: read the cost-per-step fields that HACK-013 stores.
PR: -
Evidence: -
