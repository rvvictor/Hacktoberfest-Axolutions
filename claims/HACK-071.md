# HACK-071
ID: HACK-071
State: CLAIMED
Owner: dylan-1
Branch: feat/hack-071
Worktree: /Users/dylanmartinezcastillo/Documents/Repositorios/Hackathon/Hacktoberfest-Axolutions-wt/hack-071
Worklog: worklog/WL-1793379956-dylan-1-HACK-071-hack.dstThD.md
Priority: P1
Paths: app/routers/runs.py, app/services/stages.py, app/tests/test_research_debt.py, web/src/features/project/
Depends: HACK-063, HACK-070
Verify: `uv run pytest -q && uv run ruff check app && npm --prefix web run build && bash .uak/bin/design-lint`
Lease-Until: 1793394356
Updated: 1793379956
Task-Base: 6a77b22da8dd51dd5a4dec85df4e7c718eb7dca0
Next: failing tests for the 422 cap and the log content.
PR: -
Evidence: -
Thread-Read: 0
