# HACK-071
ID: HACK-071
State: REVIEW
Owner: dylan-1
Branch: feat/hack-071
Worktree: /Users/dylanmartinezcastillo/Documents/Repositorios/Hackathon/Hacktoberfest-Axolutions-wt/hack-071
Worklog: worklog/WL-1793379956-dylan-1-HACK-071-hack.dstThD.md
Priority: P1
Paths: app/routers/runs.py, app/services/stages.py, app/tests/test_research_debt.py, web/src/features/project/
Depends: HACK-063, HACK-070
Verify: `uv run pytest -q && uv run ruff check app && npm --prefix web run build && bash .uak/bin/design-lint`
Lease-Until: 1793466944
Updated: 1793380544
Task-Base: 6a77b22da8dd51dd5a4dec85df4e7c718eb7dca0
Next: wait for review; merge on approve
PR: https://github.com/rvvictor/Hacktoberfest-Axolutions/pull/79
Evidence: Verify PASS (pytest, ruff, build, design-lint); 4 new tests seen red first; real research run reported in PR; shots 1280/390 + critic SHIP 640081b
Events: 4
Checkpoints: 1
Sessions: 2
Last-Checkpoint: 1793380544
Task-Tip: 640081b74180327bbd61313f94efd62a21acb3e4
