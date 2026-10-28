# STATE

Phase: execution
Updated: 1793208929
AVAILABLE: HACK-025 
CLAIMED: HACK-032 HACK-034 
BLOCKED: -
REVIEW: HACK-029 HACK-031 HACK-033 
INTEGRATED: (27; last 12) ... HACK-016 HACK-017 HACK-018 HACK-019 HACK-020 HACK-021 HACK-022 HACK-023 HACK-024 HACK-026 HACK-027 HACK-028 
CANCELLED: HACK-030 

Claims (first 24; status --task ID shows detail):
HACK-029 | REVIEW | sebas-2 | until 1793222864
HACK-031 | REVIEW | sebas-1 | until 1793223001
HACK-032 | CLAIMED | sebas-2 | until 1793211492
HACK-033 | REVIEW | sebas-1 | until 1793223097
HACK-034 | CLAIMED | sebas-1 | until 1793211629

Blockers: BLOCKED tasks; use status --task ID --summary.
Current decisions (last 5):
- 1793205622 | deadline lease/HACK-031/1793202355 | REQUIRES_RECOVERY | Claim kept; read the summary and use release --expired --read-summary. No work is deleted.
- 1793205934 | HACK-032 | follow-up of HACK-014 by sebas-1: Intake: under DEMO_MODE the screen never POSTs /api/runs/{id}/answers, so the run stalls at stage 2 (found by e2e/judge_
- 1793206062 | HACK-033 | follow-up of HACK-018 by sebas-1: Delivery: subscribe with named SSE events so the gate, prototype and quality events arrive and 'Aprobar entrega' appears
- 1793206185 | HACK-034 | follow-up of HACK-015 by sebas-1: Run view: guard JSON.parse on the named 'error' SSE event; when the stream closes it fires JSON.parse(undefined) | Why: 
- 1793207852 | HACK-033 | copied the run view's listen() instead of editing lib/sse.ts | Why: lib/sse.ts is owned by HACK-001, outside Paths

Global next step: available P0; else review PRs, tests, demo, rehearsal.
Why: bounded snapshot to resume without rereading history.
