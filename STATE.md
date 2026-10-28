# STATE

Phase: execution
Updated: 1793167779
AVAILABLE: HACK-024 HACK-025 
CLAIMED: HACK-008 HACK-011 
BLOCKED: -
REVIEW: HACK-019 HACK-021 
INTEGRATED: (19; last 12) ... HACK-009 HACK-010 HACK-012 HACK-013 HACK-014 HACK-015 HACK-016 HACK-017 HACK-018 HACK-020 HACK-022 HACK-023 
CANCELLED: -

Claims (first 24; status --task ID shows detail):
HACK-008 | CLAIMED | victor-1 | until 1793170479
HACK-011 | CLAIMED | sebas-1 | until 1793167798
HACK-019 | REVIEW | jabi-1 | until 1793181034
HACK-021 | REVIEW | victor-2 | until 1793180571

Blockers: BLOCKED tasks; use status --task ID --summary.
Current decisions (last 5):
- 1793166215 | HACK-007 | fixtures hand-written demo_data | Why: no LINEAR_API_KEY
- 1793166134 | HACK-019 | Explicit demo-pitch fixture, run-scoped evidence, provider errors 503 | Why: Offline demo with visible provenance and no unsupported guesses
- 1793166374 | HACK-006 | spike fixtures left as-is, flagged unverified in PR | Why: no MIRO_ACCESS_TOKEN to confirm they are real
- 1793166634 | HACK-019 | Explicit demo fixture and source-checked run-scoped Q&A; design critic SHIP; architect GO | Why: Offline usable pitch room without unsupported model claim
- 1793167756 | deadline lease/HACK-008/1793167687 | REQUIRES_RECOVERY | Claim kept; read the summary and use release --expired --read-summary. No work is deleted.

Global next step: available P0; else review PRs, tests, demo, rehearsal.
Why: bounded snapshot to resume without rereading history.
