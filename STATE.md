# STATE

Phase: execution
Updated: 1793164396
AVAILABLE: HACK-017 HACK-020 HACK-021 HACK-022 HACK-023 HACK-024 HACK-009 
CLAIMED: HACK-006 HACK-007 HACK-008 HACK-011 HACK-013 HACK-018 HACK-019 
BLOCKED: -
REVIEW: HACK-005 HACK-010 HACK-012 HACK-014 HACK-015 HACK-016 
INTEGRATED: HACK-001 HACK-002 HACK-003 HACK-004 
CANCELLED: -

Claims (first 24; status --task ID shows detail):
HACK-005 | REVIEW | dylan-2 | until 1793175250
HACK-006 | CLAIMED | fer-1 | until 1793165698
HACK-007 | CLAIMED | fer-2 | until 1793162595
HACK-008 | CLAIMED | sebas-2 | until 1793164303
HACK-010 | REVIEW | victor-2 | until 1793174707
HACK-011 | CLAIMED | sebas-1 | until 1793164305
HACK-012 | REVIEW | jabi-2 | until 1793175698
HACK-013 | CLAIMED | victor-1 | until 1793162002
HACK-014 | REVIEW | dylan-2 | until 1793178644
HACK-015 | REVIEW | dylan-2 | until 1793178400
HACK-016 | REVIEW | dylan-1 | until 1793178760
HACK-018 | CLAIMED | jabi-2 | until 1793166586
HACK-019 | CLAIMED | jabi-1 | until 1793166916

Blockers: BLOCKED tasks; use status --task ID --summary.
Current decisions (last 5):
- 1793162656 | deadline lease/HACK-007/1793162595 | REQUIRES_RECOVERY | Claim kept; read the summary and use release --expired --read-summary. No work is deleted.
- 1793163805 | deadline queue-lock/hack.47kElW-jabi-2-HACK-003/1793163805 | HUMAN | Lock lease expired; revalidate before merging
- 1793164000 | HACK-015 | local contract.ts+demo replay | Why: HACK-002 not on main
- 1793164244 | HACK-014 | local contract.ts, demo fallback | Why: HACK-002 not on main
- 1793164360 | HACK-016 | local contract.ts until HACK-002 integrates | Why: HACK-002 not on main

Global next step: available P0; else review PRs, tests, demo, rehearsal.
Why: bounded snapshot to resume without rereading history.
