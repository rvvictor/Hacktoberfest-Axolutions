# STATE

Phase: execution
Updated: 1793200362
AVAILABLE: HACK-025 
CLAIMED: HACK-029 HACK-031 
BLOCKED: -
REVIEW: -
INTEGRATED: (27; last 12) ... HACK-016 HACK-017 HACK-018 HACK-019 HACK-020 HACK-021 HACK-022 HACK-023 HACK-024 HACK-026 HACK-027 HACK-028 
CANCELLED: HACK-030 

Claims (first 24; status --task ID shows detail):
HACK-029 | CLAIMED | sebas-2 | until 1793203062
HACK-031 | CLAIMED | sebas-1 | until 1793202355

Blockers: BLOCKED tasks; use status --task ID --summary.
Current decisions (last 5):
- 1793196300 | HACK-031 | follow-up of HACK-013 by sebas-1: Cost wiring: services report usd via ctx.add_cost so real runs show non-zero cost in /api/ops (llm, voice, generator, re
- 1793196816 | HACK-024 | Ship verified recorded public demo | Why: User supplied deployment; browser and API checks pass
- 1793197570 | HACK-024 | Ship verified recorded demo on existing Render service | Why: All acceptance criteria and exact Verify pass
- 1793199655 | HACK-031 | only the pipeline-side gap is fixed | Why: no services/ stage module defines run_stage and llm.py exposes no usage, so wiring services is outside Paths an
- 1793200362 | HACK-029 | e2e drives UI; workaround posts answers and approval 3 via API where app is broken | Why: app bugs: intake skips POST answers under DEMO_MODE; delivery ne

Global next step: available P0; else review PRs, tests, demo, rehearsal.
Why: bounded snapshot to resume without rereading history.
