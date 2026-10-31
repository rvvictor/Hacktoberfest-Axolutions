# STATE

Phase: execution
Updated: 1793482646
AVAILABLE: HACK-074 HACK-080 HACK-081 HACK-083 HACK-084 HACK-085 HACK-086 HACK-087 HACK-088 HACK-089 HACK-090 
CLAIMED: -
BLOCKED: -
REVIEW: HACK-079 
INTEGRATED: (77; last 12) ... HACK-067 HACK-068 HACK-069 HACK-070 HACK-071 HACK-072 HACK-073 HACK-075 HACK-076 HACK-077 HACK-078 HACK-082 
CANCELLED: HACK-030 

Claims (first 24; status --task ID shows detail):
HACK-079 | REVIEW | dylan-2 | until 1793569017

Blockers: BLOCKED tasks; use status --task ID --summary.
Current decisions (last 5):
- 1793475896 | HACK-076 | Secure stays on everywhere else, incl. PUBLIC_URL https | Why: Safari drops Secure cookies on http://localhost -> state mismatch (server log)
- 1793477019 | HACK-075 | llm.py unchanged: contract and fallback already right; examples in prompt use other trades so idea words stay only in data block | Why: test asserts promp
- 1793479394 | HACK-077 | services/auth.py holds current_user/own_run/owner_only/paid_voice; store.py not in Paths so set_owner/run_owner use store._connect; n8n callback exempt (H
- 1793481623 | HACK-078 | own settings class in limits.py (config.py owned by HACK-076); throttle dependency on runs router and /me only; quota 429/503 returned as JSONResponse wit
- 1793482479 | HACK-079 | ApiError+sh:unauthorized event in api.ts; store.ts external store (no index.tsx so App skips it); login preflight with redirect manual to show 503 detail;

Global next step: available P0; else review PRs, tests, demo, rehearsal.
Why: bounded snapshot to resume without rereading history.
