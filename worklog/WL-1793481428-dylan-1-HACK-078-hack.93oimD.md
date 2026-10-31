# worklog/WL-1793481428-dylan-1-HACK-078-hack.93oimD.md · HACK-078

## Live summary
- Done: limits.py + runs/auth wiring + test_limits (16 tests), full suite and ruff green
- Decision: own settings class in limits.py (config.py owned by HACK-076); throttle dependency on runs router and /me only; quota 429/503 returned as JSONResponse with resets_at
- Why: stay inside Paths; detail stays a string for the web
- Failing: test_ownership fixture gave alice a project today so its POST hit the quota: added one monkeypatch line there
- Commands: bash .uak/bin/q uv run pytest -q --tb=short -x && uv run ruff check app
- Next: merge origin/main, smoke, PR, uak done

## History
- 1793481428 | CLAIMED | dylan-1 | claim; next: failing test: a second project the same UTC day answers 429 for that user
- 1793481623 | CLAIMED | dylan-1 | checkpoint; next: merge origin/main, smoke, PR, uak done
