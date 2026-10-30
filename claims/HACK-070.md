# HACK-070
ID: HACK-070
State: CLAIMED
Owner: victor-3
Branch: feat/hack-070
Worktree: /Users/victor/Documents/Proyectos/Hacktoberfest-Axolutions-wt/hack-070
Worklog: worklog/WL-1793343979-victor-3-HACK-070-hack.6rAfHw.md
Priority: P0
Paths: app/routers/runs.py, app/tests/test_retry_endpoint.py, web/src/features/project/
Depends: HACK-064
Verify: `uv run pytest -q && uv run ruff check app && npm --prefix web run build && bash .uak/bin/design-lint && uv run python e2e/judge_path.py`
Lease-Until: 1793358934
Updated: 1793344534
Task-Base: c86dc4af809e3f1ecd6bc8139c36485c4c249112
Next: read critic.txt, then uak done HACK-070 --pr URL
PR: -
Evidence: -
Thread-Read: 0
