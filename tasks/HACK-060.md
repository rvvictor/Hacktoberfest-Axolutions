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
Lease-Until: 1793426486
Updated: 1793340086
Task-Base: 89ab83e9ba5bedb101910f7626e0ade2cf2060f6
Next: Wait for review of SHA 37509ed
PR: https://github.com/rvvictor/Hacktoberfest-Axolutions/pull/70
Evidence: Verify exit 0 (pytest, ruff, build, design-lint, judge_path); smoke exit 0; recorded block idempotent; 1280x720 no overlap/scroll
Events: 4
Checkpoints: 1
Sessions: 2
Last-Checkpoint: 1793340086
Progress: 0 commit(s) since the claim · last: 89ab83e Merge pull request #64 from rvvictor/plan/hack-063-069 (25 minutes ago) · 0 uncommitted tracked file(s) · at 1793339841
Progress-Head: 89ab83e/4294967295
Progress-Changed: 1793339841
Task-Tip: 37509ed2d747382b69dd9d4014d6516b09499419
