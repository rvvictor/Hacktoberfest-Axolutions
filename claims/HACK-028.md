# HACK-028
ID: HACK-028
State: CLAIMED
Owner: victor-1
Branch: feat/hack-028
Worktree: /Users/victor/Documents/Proyectos/Hacktoberfest-Axolutions-wt/hack-028
Worklog: worklog/WL-1793194591-victor-1-HACK-028-hack.BLgEji.md
Priority: P0
Paths: app/services/pipeline.py, app/services/pitch.py, app/routers/pitch.py, app/tests/test_pitch.py, app/tests/test_pipeline.py, app/tests/test_pitch_run.py
Depends: None
Verify: `uv run pytest -q app/tests/test_pitch.py app/tests/test_pipeline.py app/tests/test_pitch_run.py`
Lease-Until: 1793197291
Updated: 1793194591
Task-Base: 8ea0211a065f113b370633897abcad824b16f449
Next: find where the pipeline emits `pitch_ready` in `app/services/pipeline.py` and persist the deck there; then add `memory.remember` calls per stage.
PR: -
Evidence: -
