# HACK-030
ID: HACK-030
State: CLAIMED
Owner: sebas-1
Branch: feat/hack-030
Worktree: /Users/sebastian/Desktop/Hackathones/Hacktoberfest-Axolutions-wt/hack-030
Worklog: worklog/WL-1793196165-sebas-1-HACK-030-hack.fMWXOT.md
Priority: P2
Paths: app/routers/ops.py, app/services/costs.py, app/tests/test_ops.py, web/src/features/ops/
Depends: None
Verify: `uv run pytest -q app/tests/test_ops.py && npm --prefix web run build && bash .uak/bin/design-lint`
Lease-Until: 1793198989
Updated: 1793196289
Task-Base: 8ea0211a065f113b370633897abcad824b16f449
Next: followup: instrument services with ctx.add_cost
PR: -
Evidence: -
