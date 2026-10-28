# STATE

Phase: execution
Updated: 1793165588
AVAILABLE: HACK-024 
CLAIMED: HACK-006 HACK-007 HACK-008 HACK-011 HACK-018 HACK-019 HACK-022 HACK-023 
BLOCKED: -
REVIEW: HACK-005 HACK-009 HACK-013 HACK-020 HACK-021 
INTEGRATED: HACK-001 HACK-002 HACK-003 HACK-004 HACK-010 HACK-012 HACK-014 HACK-015 HACK-016 HACK-017 
CANCELLED: -

Claims (first 24; status --task ID shows detail):
HACK-005 | REVIEW | dylan-2 | until 1793179855
HACK-006 | CLAIMED | fer-1 | until 1793165698
HACK-007 | CLAIMED | fer-2 | until 1793162595
HACK-008 | CLAIMED | sebas-2 | until 1793167687
HACK-009 | REVIEW | victor-1 | until 1793179988
HACK-011 | CLAIMED | sebas-1 | until 1793167798
HACK-013 | REVIEW | victor-1 | until 1793179939
HACK-018 | CLAIMED | jabi-2 | until 1793166586
HACK-019 | CLAIMED | jabi-1 | until 1793167815
HACK-020 | REVIEW | dylan-2 | until 1793179532
HACK-021 | REVIEW | victor-2 | until 1793179943
HACK-022 | CLAIMED | victor-2 | until 1793168236
HACK-023 | CLAIMED | dylan-1 | until 1793168189

Blockers: BLOCKED tasks; use status --task ID --summary.
Current decisions (last 5):
- 1793164951 | HACK-017 | versions from spec_ready events; client mode via ?mode=client toggle (Run has no mode) | Why: backend lacks versions endpoint
- 1793164988 | HACK-020 | speechSynthesis for audio, no recorded mp3 | Why: no paid API, HACK-008 absent
- 1793164996 | HACK-019 | Use integrated LLM; explicit demo run only; reject foreign and fabricated sources | Why: Preserve run scope and evidence provenance
- 1793165182 | HACK-013 | Left SSE named events as is (HACK-016 listens per type) | Why: changing breaks useBoardEvents
- 1793165271 | HACK-021 | Merged feat/hack-011 for outreach.py contract | Why: 011 not in main yet

Global next step: available P0; else review PRs, tests, demo, rehearsal.
Why: bounded snapshot to resume without rereading history.
