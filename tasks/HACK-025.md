# HACK-025
ID: HACK-025
State: CLAIMED
Owner: fer-1
Branch: feat/hack-025
Worktree: /Users/FerV/Documents/Hacktober/Hacktoberfest-Axolutions-wt/hack-025
Worklog: worklog/WL-1793211647-fer-1-HACK-025-hack.eS7jah.md
Priority: P0
Paths: app/fixtures/research/, app/fixtures/llm/, scripts/record_fixtures.py
Depends: HACK-005
Verify: `uv run pytest -q app/tests/test_research.py app/tests/test_llm.py && ! grep -rq 'example.invalid' app/fixtures/research/`
Lease-Until: 1793214347
Updated: 1793211647
Task-Base: fa2f0ffdf9b68fb2f442b9a12160498f954df5cd
Next: pedir a Fer las 3 keys en .env; luego python -m app.services.research --record
PR: -
Evidence: -
Events: 1
Checkpoints: 0
Sessions: 1
Last-Checkpoint: 0
