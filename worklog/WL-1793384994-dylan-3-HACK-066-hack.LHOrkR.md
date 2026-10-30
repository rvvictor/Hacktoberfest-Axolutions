# worklog/WL-1793384994-dylan-3-HACK-066-hack.LHOrkR.md · HACK-066

## Live summary
- Done: Claim created; implementation pending
- Decision: Own branch and worktree
- Why: Parallel work without touching the main checkout
- Failing: No validation run yet
- Commands: `uv run pytest -q && npm --prefix web run build && bash .uak/bin/design-lint && uv run python e2e/judge_path.py`
- Next: failing test that the demo deck uses `deck.json`, then the slide layout.

## History
- 1793384994 | CLAIMED | dylan-3 | claim; next: failing test that the demo deck uses `deck.json`, then the slide layout.
