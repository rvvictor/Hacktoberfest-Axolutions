# STATE

Phase: execution
Updated: 1793196686
AVAILABLE: HACK-025 HACK-029 HACK-031 
CLAIMED: HACK-024 
BLOCKED: -
REVIEW: HACK-027 HACK-028 
INTEGRATED: (24; last 12) ... HACK-013 HACK-014 HACK-015 HACK-016 HACK-017 HACK-018 HACK-019 HACK-020 HACK-021 HACK-022 HACK-023 HACK-026 
CANCELLED: HACK-030 

Claims (first 24; status --task ID shows detail):
HACK-024 | CLAIMED | jabi-1 | until 1793198991
HACK-027 | REVIEW | victor-2 | until 1793209140
HACK-028 | REVIEW | victor-1 | until 1793209168

Blockers: BLOCKED tasks; use status --task ID --summary.
Current decisions (last 5):
- 1793193594 | deadline lease/HACK-024/1793190570 | REQUIRES_RECOVERY | Claim kept; read the summary and use release --expired --read-summary. No work is deleted.
- 1793193594 | deadline decision/HACK-024-1793187236/1793188136 | REVERSIBLE_AND_LOG | Option: Ship reviewable demo documentation with public deployment explicitly unverified; Why:
- 1793194576 | plan | Victor/Victor | tasks added: HACK-027 HACK-028 HACK-029 HACK-030 | Why: backlog without PR (Plan-Channel: claims)
- 1793196289 | HACK-030 | cancel: premise already satisfied by HACK-022 | Why: real runs show cost 0 because no service calls ctx.add_cost; those files are outside HACK-030 Paths
- 1793196300 | HACK-031 | follow-up of HACK-013 by sebas-1: Cost wiring: services report usd via ctx.add_cost so real runs show non-zero cost in /api/ops (llm, voice, generator, re

Global next step: available P0; else review PRs, tests, demo, rehearsal.
Why: bounded snapshot to resume without rereading history.
