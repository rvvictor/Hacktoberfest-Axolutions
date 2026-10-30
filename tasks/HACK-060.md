# HACK-060
ID: HACK-060
State: CLAIMED
Owner: victor-3
Branch: feat/hack-060
Worktree: /Users/victor/Documents/Proyectos/Hacktoberfest-Axolutions-wt/hack-060
Worklog: worklog/WL-1793339474-victor-3-HACK-060-hack.twNTtQ.md
Priority: P1
Paths: web/src/features/live-board/demo.ts, scripts/demo_from_recordings.py, app/tests/test_demo_fixture.py
Depends: None
Verify: `uv run pytest -q && uv run ruff check app scripts && npm --prefix web run build && bash .uak/bin/design-lint && uv run python e2e/judge_path.py`
Lease-Until: 1793353874
Updated: 1793339474
Task-Base: 89ab83e9ba5bedb101910f7626e0ade2cf2060f6
Next: read `web/src/features/live-board/demo.ts` and the `WEB` table of `scripts/demo_from_recordings.py`.
PR: -
Evidence: -
Events: 1
Checkpoints: 0
Sessions: 1
Last-Checkpoint: 0
