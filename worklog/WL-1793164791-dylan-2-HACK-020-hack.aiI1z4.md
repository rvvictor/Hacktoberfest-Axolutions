# worklog/WL-1793164791-dylan-2-HACK-020-hack.aiI1z4.md · HACK-020

## Live summary
- Done: Claim created; implementation pending
- Decision: Own branch and worktree
- Why: Parallel work without touching the main checkout
- Failing: No validation run yet
- Commands: `uv run pytest -q app/tests/test_client.py && npm --prefix web run build && bash .uak/bin/design-lint`
- Next: write the barbershop fixture and `GET /api/client/demo`.

## History
- 1793164791 | CLAIMED | dylan-2 | claim; next: write the barbershop fixture and `GET /api/client/demo`.
