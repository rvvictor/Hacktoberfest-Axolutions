# HACK-025
ID: HACK-025
State: CLAIMED
Owner: dylan-3
Branch: feat/hack-025
Worktree: /Users/dylanmartinezcastillo/Documents/Repositorios/Hackathon/Hacktoberfest-Axolutions-wt/hack-025
Worklog: worklog/WL-1793211647-fer-1-HACK-025-hack.eS7jah.md
Priority: P0
Paths: app/fixtures/research/, app/fixtures/llm/, scripts/record_fixtures.py
Depends: HACK-005
Verify: `uv run pytest -q app/tests/test_research.py app/tests/test_llm.py && ! grep -rq 'example.invalid' app/fixtures/research/`
Lease-Until: 1793300348
Updated: 1793297648
Task-Base: fa2f0ffdf9b68fb2f442b9a12160498f954df5cd
Next: pedir a Fer las 3 keys en .env; luego python -m app.services.research --record
PR: -
Evidence: -
Events: 5
Checkpoints: 0
Sessions: 2
Last-Checkpoint: 0
