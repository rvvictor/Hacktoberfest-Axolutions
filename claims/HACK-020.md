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
Lease-Until: 1793179373
Updated: 1793164973
Task-Base: d3d978a833c3c5c776c1b9b86ca577727d4bd031
Next: Another agent reviews https://github.com/rvvictor/Hacktoberfest-Axolutions/pull/13; run .uak/bin/smoke
PR: https://github.com/rvvictor/Hacktoberfest-Axolutions/pull/13
Evidence: -
