# HACK-019
ID: HACK-019
State: CLAIMED
Owner: jabi-1
Branch: feat/hack-019
Worktree: /c/Users/javis/Desktop/Hacktoberfest-Axolutions-wt/hack-019
Worklog: worklog/WL-1793163961-jabi-1-HACK-019-hack.RPIBcH.md
Priority: P0
Paths: app/routers/pitch.py, app/services/pitch.py, app/tests/test_pitch.py, web/src/features/pitch/
Depends: HACK-003
Verify: `uv run pytest -q app/tests/test_pitch.py && npm --prefix web run build && bash .uak/bin/design-lint`
Lease-Until: 1793167696
Updated: 1793164996
Task-Base: 71c69e1655107e7085567d735da4683b3937ecc8
Next: Verify UI in Playwright desktop/mobile, critic, smoke, ship
PR: -
Evidence: -
