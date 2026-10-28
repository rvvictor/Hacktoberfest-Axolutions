# STATE

Phase: execution
Updated: 1793160123
AVAILABLE: HACK-009 HACK-010 HACK-014 HACK-015 HACK-016 HACK-017 HACK-018 HACK-019 HACK-020 HACK-021 HACK-022 HACK-023 HACK-024 
CLAIMED: HACK-006 HACK-007 HACK-008 HACK-011 HACK-012 HACK-013 
BLOCKED: -
REVIEW: HACK-001 HACK-002 HACK-003 HACK-004 HACK-005 
INTEGRATED: -
CANCELLED: -

Claims (first 24; status --task ID shows detail):
HACK-001 | REVIEW | victor-1 | until 1793174123
HACK-002 | REVIEW | victor-2 | until 1793173500
HACK-003 | REVIEW | dylan-1 | until 1793173842
HACK-004 | REVIEW | victor-2 | until 1793173648
HACK-005 | REVIEW | dylan-2 | until 1793173681
HACK-006 | CLAIMED | fer-1 | until 1793162585
HACK-007 | CLAIMED | fer-2 | until 1793162595
HACK-008 | CLAIMED | sebas-2 | until 1793162595
HACK-011 | CLAIMED | sebas-1 | until 1793162699
HACK-012 | CLAIMED | sebas-3 | until 1793162823
HACK-013 | CLAIMED | victor-1 | until 1793162002

Blockers: BLOCKED tasks; use status --task ID --summary.
Current decisions (last 5):
- 1793159442 | HACK-003 | Direction 3 Línea 1 | Why: human pick
- 1793159885 | HACK-006 | tests con asyncio.run, sin pytest-asyncio | Why: evitar tocar pyproject compartido
- 1793159895 | HACK-007 | fixtures hand-written, no LINEAR key | Why: cannot record real call
- 1793159895 | HACK-008 | httpx direct to ElevenLabs REST (respx-mocked), not SDK; fixtures are placeholders marked demo_data | Why: no API key yet; keeps tests offline
- 1793160123 | HACK-012 | CI-only checks (build, lint, gitleaks, npm audit, smoke) are named in report.details, not reported as passed; QualityCheck has no 'skipped' state | Why: r

Global next step: available P0; else review PRs, tests, demo, rehearsal.
Why: bounded snapshot to resume without rereading history.
