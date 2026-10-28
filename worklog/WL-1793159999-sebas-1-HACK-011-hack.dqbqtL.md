# worklog/WL-1793159999-sebas-1-HACK-011-hack.dqbqtL.md · HACK-011

## Live summary
- Done: outreach service (draft, approval gate, opt-out, signed n8n hand-off, in-process fallback), n8n workflow export + README, fictitious fixtures, 18 tests
- Decision: nothing sent without approved_by; opt-out line appended in code; opted-out prospects skipped before any n8n call; in-process fallback; mock send only
- Why: acceptance rules enforced in code and tested, not only in UI
- Failing: ruff UP017 (timezone.utc) fixed
- Commands: bash .uak/bin/q uv run pytest -q app/tests/test_outreach.py -> OK 18 passed; bash .uak/bin/q uv run pytest -q -> OK 23 passed
- Next: wait for HACK-001/002 INTEGRATED, then uak done HACK-011; hunter router owns /api/hunter/outreach/{id}/callback and must call verify_callback + apply_callback (not in my Paths)

## History
- 1793159999 | CLAIMED | sebas-1 | claim; next: write the in-process flow in `outreach.py`, then mirror it in n8n. Hosting n8n (Cloud or Docker) needs a human's OK.
- 1793160148 | CLAIMED | sebas-1 | checkpoint; next: wait for HACK-001/002 INTEGRATED, then uak done HACK-011; hunter router owns /api/hunter/outreach/{id}/callback and must call verify_callback + apply_callback (not in my Paths)
- 1793160782 | CLAIMED | sebas-1 | heartbeat; lease until 1793163482
- 1793161605 | CLAIMED | sebas-1 | heartbeat; lease until 1793164305
- 1793165098 | CLAIMED | sebas-1 | heartbeat; lease until 1793167798
- 1793167889 | AVAILABLE | victor-2 | release; claim released by victor-2; reason: -; summary kept
- 1793167895 | CLAIMED | victor-2 | claim; next: wait for HACK-001/002 INTEGRATED, then uak done HACK-011; hunter router owns /api/hunter/outreach/{id}/callback and must call verify_callback + apply_callback (not in my Paths)
