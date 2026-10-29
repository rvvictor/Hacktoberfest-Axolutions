# worklog/WL-1793312785-dylan-1-HACK-051-hack.EEFv7O.md · HACK-051

## Live summary
- Done: Claim created; implementation pending
- Decision: Own branch and worktree
- Why: Parallel work without touching the main checkout
- Failing: No validation run yet
- Commands: `uv run pytest -q && uv run ruff check app && npm --prefix web run build && bash .uak/bin/design-lint && uv run python e2e/judge_path.py`
- Next: in pipeline `_produce`, allow stages 7-8 through `_provider` under DEMO_MODE; then the project card iframe.

## History
- 1793312785 | CLAIMED | dylan-1 | claim; next: in pipeline `_produce`, allow stages 7-8 through `_provider` under DEMO_MODE; then the project card iframe.
