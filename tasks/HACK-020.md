# HACK-020
ID: HACK-020
State: REVIEW
Owner: dylan-2
Branch: feat/hack-020
Worktree: /Users/dylanmartinezcastillo/Documents/Repositorios/Hackathon/Hacktoberfest-Axolutions-wt/hack-020
Worklog: worklog/WL-1793164791-dylan-2-HACK-020-hack.aiI1z4.md
Priority: P1
Paths: app/routers/client.py, app/fixtures/client/, app/tests/test_client.py, web/src/features/client/
Depends: HACK-003
Verify: `uv run pytest -q app/tests/test_client.py && npm --prefix web run build && bash .uak/bin/design-lint`
Lease-Until: 1793179388
Updated: 1793164988
Task-Base: d3d978a833c3c5c776c1b9b86ca577727d4bd031
Next: Wait for review
PR: https://github.com/rvvictor/Hacktoberfest-Axolutions/pull/13
Evidence: pytest test_client 4 passed; npm build ok; design-lint PASS; smoke PRODUCT_PASS
Events: 3
Checkpoints: 1
Sessions: 1
Last-Checkpoint: 1793164988
Task-Tip: a0f84e0a56f7335f245a85fec9d69f23b7b5030c
