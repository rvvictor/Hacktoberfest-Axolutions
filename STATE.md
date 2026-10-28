# STATE

Phase: execution
Updated: 1793216799
AVAILABLE: -
CLAIMED: HACK-025 
BLOCKED: -
REVIEW: HACK-035 
INTEGRATED: (32; last 12) ... HACK-021 HACK-022 HACK-023 HACK-024 HACK-026 HACK-027 HACK-028 HACK-029 HACK-031 HACK-032 HACK-033 HACK-034 
CANCELLED: HACK-030 

Claims (first 24; status --task ID shows detail):
HACK-025 | CLAIMED | fer-1 | until 1793214347
HACK-035 | REVIEW | dylan-1 | until 1793228512

Blockers: BLOCKED tasks; use status --task ID --summary.
Current decisions (last 5):
- 1793207852 | HACK-033 | copied the run view's listen() instead of editing lib/sse.ts | Why: lib/sse.ts is owned by HACK-001, outside Paths
- 1793209191 | HACK-034 | same guard as delivery listen() | Why: browser error event has no data when the stream closes
- 1793209299 | HACK-032 | offline flag separate from demo_data badge | Why: demo_data is true for real runs under DEMO_MODE, so it cannot signal the offline sample
- 1793213990 | HACK-035 | follow-up of HACK-011 by dylan-1: n8n Cloud: read N8N_WEBHOOK_SECRET and SPEEDHACK_API_URL from $vars instead of $env | Why: same Paths, no scope change
- 1793214723 | deadline lease/HACK-025/1793214347 | REQUIRES_RECOVERY | Claim kept; read the summary and use release --expired --read-summary. No work is deleted.

Global next step: available P0; else review PRs, tests, demo, rehearsal.
Why: bounded snapshot to resume without rereading history.
