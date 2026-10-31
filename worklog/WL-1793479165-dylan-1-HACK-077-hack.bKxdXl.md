# worklog/WL-1793479165-dylan-1-HACK-077-hack.bKxdXl.md · HACK-077

## Live summary
- Done: ownership deps (401/404/403), owner_id on create, tests
- Decision: services/auth.py holds current_user/own_run/owner_only/paid_voice; store.py not in Paths so set_owner/run_owner use store._connect; n8n callback exempt (HMAC); anonymous gets 403 on hunter/ops; voice open in DEMO_MODE
- Why: plan.md Design: dependencies per route, no-op while AUTH_REQUIRED false
- Failing: none
- Commands: bash .uak/bin/q uv run pytest -q --tb=short -x && uv run ruff check app
- Next: merge origin/main, smoke, PR, uak done

## History
- 1793479165 | CLAIMED | dylan-1 | claim; next: failing test: GET a run without a session answers 401 when AUTH_REQUIRED
- 1793479394 | CLAIMED | dylan-1 | checkpoint; next: merge origin/main, smoke, PR, uak done
