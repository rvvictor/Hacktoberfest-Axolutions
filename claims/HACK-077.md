# HACK-077
ID: HACK-077
State: CLAIMED
Owner: dylan-1
Branch: feat/hack-077
Worktree: /Users/dylanmartinezcastillo/Documents/Repositorios/Hackathon/Hacktoberfest-Axolutions-wt/hack-077
Worklog: worklog/WL-1793479165-dylan-1-HACK-077-hack.bKxdXl.md
Priority: P0
Paths: app/routers/runs.py, app/routers/pitch.py, app/routers/prototypes.py, app/routers/voice.py, app/routers/hunter.py, app/routers/ops.py, app/services/auth.py, app/tests/test_ownership.py
Depends: HACK-076
Verify: `uv run pytest -q && uv run ruff check app`
Lease-Until: 1793493565
Updated: 1793479165
Task-Base: a46fa99915c167753aecfa3d88bbb2d346d7d026
Next: failing test: GET a run without a session answers 401 when AUTH_REQUIRED
PR: -
Evidence: -
Thread-Read: 0
