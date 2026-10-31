# HACK-079
ID: HACK-079
State: REVIEW
Owner: dylan-2
Branch: feat/hack-079
Worktree: /Users/dylanmartinezcastillo/Documents/Repositorios/Hackathon/Hacktoberfest-Axolutions-wt/hack-079
Worklog: worklog/WL-1793482200-dylan-2-HACK-079-hack.fWJCmD.md
Priority: P0
Paths: web/src/lib/api.ts, web/src/lib/types.ts, web/src/App.tsx, web/src/features/account/, web/src/features/intake/, e2e/judge_path.py
Depends: HACK-076
Verify: `npm --prefix web run build && bash .uak/bin/design-lint && uv run python e2e/judge_path.py`
Lease-Until: 1793569017
Updated: 1793482617
Task-Base: 140d906035847b39cd93c6f61d4650de6bba9a7b
Next: Humano: Queue/base push rejected; check remote, atomic push and permissions
PR: https://github.com/rvvictor/Hacktoberfest-Axolutions/pull/95
Evidence: build, oxlint, design-lint, ruff, pytest, e2e/judge_path.py PASS, smoke PASS at 1998905; Playwright 1280/390 shots in .uak-shots/HACK-079; critic SHIP 1998905
Events: 5
Checkpoints: 1
Sessions: 2
Last-Checkpoint: 1793482479
Task-Tip: 1998905691b7a7e11f9d858ea1212f74d375a1d5
