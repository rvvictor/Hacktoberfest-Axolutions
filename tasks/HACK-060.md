# HACK-060
ID: HACK-060
State: REVIEW
Owner: victor-3
Branch: feat/hack-060
Worktree: /Users/victor/Documents/Proyectos/Hacktoberfest-Axolutions-wt/hack-060
Worklog: worklog/WL-1793339474-victor-3-HACK-060-hack.twNTtQ.md
Priority: P1
Paths: web/src/features/live-board/demo.ts, scripts/demo_from_recordings.py, app/tests/test_demo_fixture.py
Depends: None
Verify: `uv run pytest -q && uv run ruff check app scripts && npm --prefix web run build && bash .uak/bin/design-lint && uv run python e2e/judge_path.py`
Lease-Until: 1793427485
Updated: 1793341085
Task-Base: 89ab83e9ba5bedb101910f7626e0ade2cf2060f6
Next: Another agent reviews https://github.com/rvvictor/Hacktoberfest-Axolutions/pull/70; run .uak/bin/smoke
PR: https://github.com/rvvictor/Hacktoberfest-Axolutions/pull/70
Evidence: Verify exit 0; new test_live_board_example_is_the_recorded_board_and_backlog
Events: 8
Checkpoints: 1
Sessions: 4
Last-Checkpoint: 1793340086
Progress: 5 commit(s) since the claim · last: e57efdf HACK-060: test the live-board example equals the recorded board and backlog (8 minutes ago) · 0 uncommitted tracked file(s) · at 1793341085
Progress-Head: e57efdf/4294967295
Progress-Changed: 1793341085
Task-Tip: e57efdfbb9a377c7e453421814fff5c8b5600b8c
