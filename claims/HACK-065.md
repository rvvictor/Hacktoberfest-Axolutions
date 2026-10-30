# HACK-065
ID: HACK-065
State: CLAIMED
Owner: victor-2
Branch: feat/hack-065
Worktree: /Users/victor/Documents/Proyectos/Hacktoberfest-Axolutions-wt/hack-065
Worklog: worklog/WL-1793339454-victor-2-HACK-065-hack.B0kNJY.md
Priority: P0
Paths: app/services/pitch.py, app/services/voice.py, app/routers/pitch.py, app/services/prompts/narration.md, app/fixtures/voice/, app/tests/test_pitch_narration.py, web/src/features/pitch/
Depends: None
Verify: `uv run pytest -q && uv run ruff check app && npm --prefix web run build && bash .uak/bin/design-lint && uv run python e2e/judge_path.py`
Lease-Until: 1793354248
Updated: 1793339848
Task-Base: 89ab83e9ba5bedb101910f7626e0ade2cf2060f6
Next: failing test for the per-slide script validation, then the narration endpoint.
PR: -
Evidence: -
Thread-Read: 213
