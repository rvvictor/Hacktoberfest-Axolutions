# STATE

Phase: execution
Updated: 1793480031
AVAILABLE: HACK-074 HACK-078 HACK-079 HACK-080 HACK-081 HACK-083 HACK-084 HACK-085 HACK-086 HACK-087 
CLAIMED: -
BLOCKED: -
REVIEW: HACK-077 HACK-082 
INTEGRATED: (74; last 12) ... HACK-064 HACK-065 HACK-066 HACK-067 HACK-068 HACK-069 HACK-070 HACK-071 HACK-072 HACK-073 HACK-075 HACK-076 
CANCELLED: HACK-030 

Claims (first 24; status --task ID shows detail):
HACK-077 | REVIEW | dylan-1 | until 1793565897
HACK-082 | REVIEW | dylan-2 | until 1793561746

Blockers: BLOCKED tasks; use status --task ID --summary.
Current decisions (last 5):
- 1793471797 | HACK-076 | no JWT lib: id_token from token endpoint over TLS (OIDC 3.1.3.7); runs_per_day falls back to default because conftest nulls settings | Why: spec 001 plan
- 1793475678 | deadline decision/HACK-082-1793471398/1793472298 | BLOCKED_OTHER_TASK | Option: uv add mcp cryptography (pyproject.toml, uv.lock); Why: ADR 0003 (accepted by Dylan) 
- 1793475896 | HACK-076 | Secure stays on everywhere else, incl. PUBLIC_URL https | Why: Safari drops Secure cookies on http://localhost -> state mismatch (server log)
- 1793477019 | HACK-075 | llm.py unchanged: contract and fallback already right; examples in prompt use other trades so idea words stay only in data block | Why: test asserts promp
- 1793479394 | HACK-077 | services/auth.py holds current_user/own_run/owner_only/paid_voice; store.py not in Paths so set_owner/run_owner use store._connect; n8n callback exempt (H

Global next step: available P0; else review PRs, tests, demo, rehearsal.
Why: bounded snapshot to resume without rereading history.
