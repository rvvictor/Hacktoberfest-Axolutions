# HACK-020
ID: HACK-020
State: CLAIMED
Owner: dylan-2
Branch: feat/hack-020
Worktree: /Users/dylanmartinezcastillo/Documents/Repositorios/Hackathon/Hacktoberfest-Axolutions-wt/hack-020
Worklog: worklog/WL-1793164791-dylan-2-HACK-020-hack.aiI1z4.md
Priority: P1
Paths: app/routers/client.py, app/fixtures/client/, app/tests/test_client.py, web/src/features/client/
Depends: HACK-003
Verify: `uv run pytest -q app/tests/test_client.py && npm --prefix web run build && bash .uak/bin/design-lint`
Lease-Until: 1793167491
Updated: 1793164791
Task-Base: d3d978a833c3c5c776c1b9b86ca577727d4bd031
Next: write the barbershop fixture and `GET /api/client/demo`.
PR: -
Evidence: -
Events: 1
Checkpoints: 0
Sessions: 1
Last-Checkpoint: 0
