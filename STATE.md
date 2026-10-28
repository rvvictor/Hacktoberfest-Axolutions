# STATE

Phase: execution
Updated: 1793160360
AVAILABLE: HACK-014 HACK-015 HACK-016 HACK-017 HACK-018 HACK-019 HACK-020 HACK-021 HACK-022 HACK-023 HACK-024 HACK-012 
CLAIMED: HACK-006 HACK-007 HACK-008 HACK-009 HACK-011 HACK-013 
BLOCKED: -
REVIEW: HACK-001 HACK-002 HACK-003 HACK-004 HACK-005 HACK-010 
INTEGRATED: -
CANCELLED: -

Claims (first 24; status --task ID shows detail):
HACK-001 | REVIEW | victor-1 | until 1793174123
HACK-002 | REVIEW | victor-2 | until 1793174617
HACK-003 | REVIEW | dylan-1 | until 1793173842
HACK-004 | REVIEW | victor-2 | until 1793174619
HACK-005 | REVIEW | dylan-2 | until 1793173681
HACK-006 | CLAIMED | fer-1 | until 1793162585
HACK-007 | CLAIMED | fer-2 | until 1793162595
HACK-008 | CLAIMED | sebas-2 | until 1793162595
HACK-009 | CLAIMED | jabi-1 | until 1793162810
HACK-010 | REVIEW | victor-2 | until 1793174707
HACK-011 | CLAIMED | sebas-1 | until 1793162848
HACK-013 | CLAIMED | victor-1 | until 1793162002

Blockers: BLOCKED tasks; use status --task ID --summary.
Current decisions (last 5):
- 1793159895 | HACK-008 | httpx direct to ElevenLabs REST (respx-mocked), not SDK; fixtures are placeholders marked demo_data | Why: no API key yet; keeps tests offline
- 1793160123 | HACK-012 | CI-only checks (build, lint, gitleaks, npm audit, smoke) are named in report.details, not reported as passed; QualityCheck has no 'skipped' state | Why: r
- 1793160148 | HACK-011 | nothing sent without approved_by; opt-out line appended in code; opted-out prospects skipped before any n8n call; in-process fallback; mock send only | Wh
- 1793160199 | deadline decision/HACK-003-1793159298/1793160198 | BLOCKED_OTHER_TASK | Option: Direction 3 · Línea 1; Why: Dylan picked it looking at the gallery: the 9 stages an
- 1793160307 | HACK-010 | Prompt built only from Spec/BacklogItem fields; plan B url = LOVABLE_PREBUILT_URL or /fixtures/generator/planb/index.html (router must serve it) | Why: no

Global next step: available P0; else review PRs, tests, demo, rehearsal.
Why: bounded snapshot to resume without rereading history.
