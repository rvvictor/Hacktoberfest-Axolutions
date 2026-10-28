# STATE

Phase: execution
Updated: 1793205622
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
- 1793197570 | HACK-024 | Ship verified recorded demo on existing Render service | Why: All acceptance criteria and exact Verify pass
- 1793199655 | HACK-031 | only the pipeline-side gap is fixed | Why: no services/ stage module defines run_stage and llm.py exposes no usage, so wiring services is outside Paths an
- 1793200362 | HACK-029 | e2e drives UI; workaround posts answers and approval 3 via API where app is broken | Why: app bugs: intake skips POST answers under DEMO_MODE; delivery ne
- 1793205622 | deadline lease/HACK-029/1793203062 | REQUIRES_RECOVERY | Claim kept; read the summary and use release --expired --read-summary. No work is deleted.
- 1793205622 | deadline lease/HACK-031/1793202355 | REQUIRES_RECOVERY | Claim kept; read the summary and use release --expired --read-summary. No work is deleted.

Global next step: available P0; else review PRs, tests, demo, rehearsal.
Why: bounded snapshot to resume without rereading history.
