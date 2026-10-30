# HACK-066
ID: HACK-066
State: CLAIMED
Owner: dylan-3
Branch: feat/hack-066
Worktree: /Users/dylanmartinezcastillo/Documents/Repositorios/Hackathon/Hacktoberfest-Axolutions-wt/hack-066
Worklog: worklog/WL-1793384994-dylan-3-HACK-066-hack.LHOrkR.md
Priority: P0
Paths: web/src/features/pitch/, app/services/pitch.py, app/tests/test_pitch_deck.py
Depends: None
Verify: `uv run pytest -q && npm --prefix web run build && bash .uak/bin/design-lint && uv run python e2e/judge_path.py`
Lease-Until: 1793399394
Updated: 1793384994
Task-Base: 686a57431b016f535deaf468833791e2300ac886
Next: failing test that the demo deck uses `deck.json`, then the slide layout.
PR: -
Evidence: -
Events: 2
Checkpoints: 0
Sessions: 1
Last-Checkpoint: 0
