# HACK-072
ID: HACK-072
State: CLAIMED
Owner: victor-3
Branch: feat/hack-072
Worktree: /Users/victor/Documents/Proyectos/Hacktoberfest-Axolutions-wt/hack-072
Worklog: worklog/WL-1793405790-victor-3-HACK-072-hack.G47eOf.md
Priority: P1
Paths: app/services/pitch.py, app/services/voice.py, app/config.py, app/tests/test_narration_spend.py
Depends: HACK-065
Verify: `uv run pytest -q && uv run ruff check app`
Lease-Until: 1793420190
Updated: 1793405790
Task-Base: 70c03b4dcc4f77270f80cb63b3a7e58242799656
Next: failing test: two concurrent `narrate()` calls for one slide, counting the TTS stub's calls.
PR: -
Evidence: -
Thread-Read: 0
