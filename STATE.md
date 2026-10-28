# STATE

Phase: execution
Updated: 1793161980
AVAILABLE: HACK-014 HACK-015 HACK-016 HACK-017 HACK-018 HACK-019 HACK-020 HACK-021 HACK-022 HACK-023 HACK-024 
CLAIMED: HACK-006 HACK-007 HACK-008 HACK-011 HACK-013 
BLOCKED: HACK-009 
REVIEW: HACK-001 HACK-002 HACK-003 HACK-004 HACK-005 HACK-010 HACK-012 
INTEGRATED: -
CANCELLED: -

Claims (first 24; status --task ID shows detail):
HACK-001 | REVIEW | victor-1 | until 1793174123
HACK-002 | REVIEW | victor-2 | until 1793174617
HACK-003 | REVIEW | dylan-1 | until 1793173842
HACK-004 | REVIEW | victor-2 | until 1793174619
HACK-005 | REVIEW | dylan-2 | until 1793175250
HACK-006 | CLAIMED | fer-1 | until 1793163992
HACK-007 | CLAIMED | fer-2 | until 1793162595
HACK-008 | CLAIMED | sebas-2 | until 1793164303
HACK-009 | BLOCKED | jabi-1 | until 1793164667
HACK-010 | REVIEW | victor-2 | until 1793174707
HACK-011 | CLAIMED | sebas-1 | until 1793164305
HACK-012 | REVIEW | jabi-2 | until 1793175698
HACK-013 | CLAIMED | victor-1 | until 1793162002

Blockers: BLOCKED tasks; use status --task ID --summary.
Current decisions (last 5):
- 1793160123 | HACK-012 | CI-only checks (build, lint, gitleaks, npm audit, smoke) are named in report.details, not reported as passed; QualityCheck has no 'skipped' state | Why: r
- 1793160148 | HACK-011 | nothing sent without approved_by; opt-out line appended in code; opted-out prospects skipped before any n8n call; in-process fallback; mock send only | Wh
- 1793160199 | deadline decision/HACK-003-1793159298/1793160198 | BLOCKED_OTHER_TASK | Option: Direction 3 · Línea 1; Why: Dylan picked it looking at the gallery: the 9 stages an
- 1793160307 | HACK-010 | Prompt built only from Spec/BacklogItem fields; plan B url = LOVABLE_PREBUILT_URL or /fixtures/generator/planb/index.html (router must serve it) | Why: no
- 1793161562 | HACK-009 | Missing key uses process-local keyword cache and honest local demo recording | Why: No Backboard key or prior recording exists; preserve source provenance

Global next step: available P0; else review PRs, tests, demo, rehearsal.
Why: bounded snapshot to resume without rereading history.
