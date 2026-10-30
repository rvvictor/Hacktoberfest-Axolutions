# worklog/WL-1793381166-dylan-3-HACK-061-hack.8TFNiI.md · HACK-061

## Live summary
- Done: Claim created; implementation pending
- Decision: Own branch and worktree
- Why: Parallel work without touching the main checkout
- Failing: No validation run yet
- Commands: `uv run pytest -q && uv run ruff check app && uv run python e2e/judge_path.py`
- Next: read `ask()` and `_words()`; measure which passages each question keeps today before changing the rule.

## History
- 1793381166 | CLAIMED | dylan-3 | claim; next: read `ask()` and `_words()`; measure which passages each question keeps today before changing the rule.
