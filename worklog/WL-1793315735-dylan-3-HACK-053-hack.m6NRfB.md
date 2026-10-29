# worklog/WL-1793315735-dylan-3-HACK-053-hack.m6NRfB.md · HACK-053

## Live summary
- Done: Claim created; implementation pending
- Decision: Own branch and worktree
- Why: Parallel work without touching the main checkout
- Failing: No validation run yet
- Commands: `uv run pytest -q && uv run ruff check app scripts && ! grep -q 'example.invalid\|Placeholder' app/fixtures/demo/run.jsonl web/src/features/project/demo.ts web/src/features/spec/demo.ts && npm --prefix web run build && bash .uak/bin/design-lint && uv run python e2e/judge_path.py`
- Next: read how pipeline `_fixture` replays stage 3/4 and what `_record` stores for spec_ready; write the script, run it, diff run.jsonl.

## History
- 1793315735 | CLAIMED | dylan-3 | claim; next: read how pipeline `_fixture` replays stage 3/4 and what `_record` stores for spec_ready; write the script, run it, diff run.jsonl.
