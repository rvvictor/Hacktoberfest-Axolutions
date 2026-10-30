# HACK-064
ID: HACK-064
State: CLAIMED
Owner: sebas-1
Branch: feat/hack-064
Worktree: /Users/sebastian/Desktop/Hackathones/Hacktoberfest-Axolutions-wt/hack-064
Worklog: worklog/WL-1793341858-sebas-1-HACK-064-hack.eXEMBX.md
Priority: P0
Paths: app/services/pipeline.py, app/services/miro.py, app/services/stages.py, app/tests/test_live_failures.py, web/src/features/project/
Depends: None
Verify: `uv run pytest -q && uv run ruff check app && npm --prefix web run build && bash .uak/bin/design-lint && uv run python e2e/judge_path.py`
Lease-Until: 1793357003
Updated: 1793342603
Task-Base: d92026db547cd029f55cb062e4690a476e48b4b7
Next: PR + done; HACK-070 does endpoint + card
PR: -
Evidence: -
Thread-Read: 0
