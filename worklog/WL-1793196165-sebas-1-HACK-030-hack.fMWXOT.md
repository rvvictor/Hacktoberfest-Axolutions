# worklog/WL-1793196165-sebas-1-HACK-030-hack.fMWXOT.md · HACK-030

## Live summary
- Done: no code change: costs.py already reads real store; Verify passes on main (pytest test_ops 3, web build, design-lint PASS)
- Decision: cancel: premise already satisfied by HACK-022
- Why: real runs show cost 0 because no service calls ctx.add_cost; those files are outside HACK-030 Paths
- Failing: -
- Commands: bash .uak/bin/q uv run pytest -q app/tests/test_ops.py
- Next: followup: instrument services with ctx.add_cost

## History
- 1793196165 | CLAIMED | sebas-1 | claim; next: read the cost fields `app/services/store.py` saves per run, then replace the fixture in `app/services/costs.py`.
- 1793196289 | CLAIMED | sebas-1 | checkpoint; next: followup: instrument services with ctx.add_cost
