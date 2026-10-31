# HACK-076
ID: HACK-076
State: CLAIMED
Owner: dylan-3
Branch: feat/hack-076
Worktree: /Users/dylanmartinezcastillo/Documents/Repositorios/Hackathon/Hacktoberfest-Axolutions-wt/hack-076
Worklog: worklog/WL-1793471336-dylan-3-HACK-076-hack.CD2WQ9.md
Priority: P0
Paths: app/routers/auth.py, app/services/auth.py, app/services/store.py, app/config.py, app/tests/test_auth_google.py, .env.example
Depends: None
Verify: `uv run pytest -q && uv run ruff check app`
Lease-Until: 1793485736
Updated: 1793471336
Task-Base: 9f9cb50015a908400c93009d321cefb3ee42f6ce
Next: failing test: callback with a wrong `state` creates no session.
PR: -
Evidence: -
Thread-Read: 0
