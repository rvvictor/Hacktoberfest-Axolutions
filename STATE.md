# STATE

Phase: execution
Updated: 1793165072
AVAILABLE: HACK-021 HACK-022 HACK-023 HACK-024 HACK-009 
CLAIMED: HACK-006 HACK-007 HACK-008 HACK-011 HACK-013 HACK-018 HACK-019 
BLOCKED: -
REVIEW: HACK-005 HACK-014 HACK-015 HACK-016 HACK-017 HACK-020 
INTEGRATED: HACK-001 HACK-002 HACK-003 HACK-004 HACK-010 HACK-012 
CANCELLED: -

Claims (first 24; status --task ID shows detail):
HACK-005 | REVIEW | dylan-2 | until 1793175250
HACK-006 | CLAIMED | fer-1 | until 1793165698
HACK-007 | CLAIMED | fer-2 | until 1793162595
HACK-008 | CLAIMED | sebas-2 | until 1793164303
HACK-011 | CLAIMED | sebas-1 | until 1793164305
HACK-013 | CLAIMED | victor-1 | until 1793162002
HACK-014 | REVIEW | dylan-2 | until 1793178644
HACK-015 | REVIEW | dylan-2 | until 1793178829
HACK-016 | REVIEW | dylan-1 | until 1793178760
HACK-017 | REVIEW | dylan-1 | until 1793179351
HACK-018 | CLAIMED | jabi-2 | until 1793166586
HACK-019 | CLAIMED | jabi-1 | until 1793167696
HACK-020 | REVIEW | dylan-2 | until 1793179472

Blockers: BLOCKED tasks; use status --task ID --summary.
Current decisions (last 5):
- 1793164497 | deadline lease/HACK-008/1793164303 | REQUIRES_RECOVERY | Claim kept; read the summary and use release --expired --read-summary. No work is deleted.
- 1793164497 | deadline lease/HACK-011/1793164305 | REQUIRES_RECOVERY | Claim kept; read the summary and use release --expired --read-summary. No work is deleted.
- 1793164951 | HACK-017 | versions from spec_ready events; client mode via ?mode=client toggle (Run has no mode) | Why: backend lacks versions endpoint
- 1793164988 | HACK-020 | speechSynthesis for audio, no recorded mp3 | Why: no paid API, HACK-008 absent
- 1793164996 | HACK-019 | Use integrated LLM; explicit demo run only; reject foreign and fabricated sources | Why: Preserve run scope and evidence provenance

Global next step: available P0; else review PRs, tests, demo, rehearsal.
Why: bounded snapshot to resume without rereading history.
