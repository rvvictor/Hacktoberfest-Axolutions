# HACK-054
ID: HACK-054
State: CLAIMED
Owner: dylan-3
Branch: feat/hack-054
Worktree: /Users/dylanmartinezcastillo/Documents/Repositorios/Hackathon/Hacktoberfest-Axolutions-wt/hack-054
Worklog: worklog/WL-1793317115-dylan-3-HACK-054-hack.FgGdGM.md
Priority: P1
Paths: app/fixtures/demo/, web/src/features/project/demo.ts, web/src/features/spec/demo.ts, scripts/demo_from_recordings.py, app/tests/test_demo_fixture.py, app/tests/test_schemas.py
Depends: HACK-053
Verify: `uv run pytest -q && uv run ruff check app scripts && ! grep -q 'example.invalid\|Placeholder' app/fixtures/demo/run.jsonl web/src/features/project/demo.ts web/src/features/spec/demo.ts && npm --prefix web run build && bash .uak/bin/design-lint && uv run python e2e/judge_path.py`
Lease-Until: 1793319815
Updated: 1793317115
Task-Base: ceb05aadd61dcd19fb93055271262f9cf77ba3ae
Next: Implement HACK-054 and run: `uv run pytest -q && uv run ruff check app scripts && ! grep -q 'example.invalid\|Placeholder' app/fixtures/demo/run.jsonl web/src/features/project/demo.ts web/src/features/spec/demo.ts && npm --prefix web run build && bash .uak/bin/design-lint && uv run python e2e/judge_path.py`
PR: -
Evidence: -
