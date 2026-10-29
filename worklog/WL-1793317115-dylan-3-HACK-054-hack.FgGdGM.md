# worklog/WL-1793317115-dylan-3-HACK-054-hack.FgGdGM.md · HACK-054

## Live summary
- Done: Claim created; implementation pending
- Decision: Own branch and worktree
- Why: Parallel work without touching the main checkout
- Failing: No validation run yet
- Commands: `uv run pytest -q && uv run ruff check app scripts && ! grep -q 'example.invalid\|Placeholder' app/fixtures/demo/run.jsonl web/src/features/project/demo.ts web/src/features/spec/demo.ts && npm --prefix web run build && bash .uak/bin/design-lint && uv run python e2e/judge_path.py`
- Next: Implement HACK-054 and run: `uv run pytest -q && uv run ruff check app scripts && ! grep -q 'example.invalid\|Placeholder' app/fixtures/demo/run.jsonl web/src/features/project/demo.ts web/src/features/spec/demo.ts && npm --prefix web run build && bash .uak/bin/design-lint && uv run python e2e/judge_path.py`

## History
- 1793317115 | CLAIMED | dylan-3 | claim; next: Implement HACK-054 and run: `uv run pytest -q && uv run ruff check app scripts && ! grep -q 'example.invalid\|Placeholder' app/fixtures/demo/run.jsonl web/src/features/project/demo.ts web/src/features/spec/demo.ts && npm --prefix web run build && bash .uak/bin/design-lint && uv run python e2e/judge_path.py`
- 1793317422 | CLAIMED | dylan-3 | pending decision HACK-054-1793317422; option: test_schemas.py: demo fixture needs >= 6 linear issues (the recorded backlog), not >= 8; Miro stays >= 12 (the live board code emits 15); Why: the 8 described the placeholder fixture; the backlog prompt sets no count and inventing issues is forbidden; Dylan chose this over re-recording
