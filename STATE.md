# STATE

Phase: execution
Updated: 1793194602
AVAILABLE: HACK-025 HACK-029 HACK-030 
CLAIMED: HACK-027 HACK-028 
BLOCKED: HACK-024 
REVIEW: -
INTEGRATED: (24; last 12) ... HACK-013 HACK-014 HACK-015 HACK-016 HACK-017 HACK-018 HACK-019 HACK-020 HACK-021 HACK-022 HACK-023 HACK-026 
CANCELLED: -

Claims (first 24; status --task ID shows detail):
HACK-024 | BLOCKED | jabi-1 | until 1793190570
HACK-027 | CLAIMED | victor-2 | until 1793197297
HACK-028 | CLAIMED | victor-1 | until 1793197291

Blockers: BLOCKED tasks; use status --task ID --summary.
Current decisions (last 5):
- 1793187567 | HACK-024 | Keep deployment URL pending and expose gap in PR | Why: No existing public URL found; human requested
- 1793187870 | HACK-024 | Keep draft until public deployment URL is supplied | Why: Task acceptance requires judge-accessible URL; none found or supplied
- 1793193594 | deadline lease/HACK-024/1793190570 | REQUIRES_RECOVERY | Claim kept; read the summary and use release --expired --read-summary. No work is deleted.
- 1793193594 | deadline decision/HACK-024-1793187236/1793188136 | REVERSIBLE_AND_LOG | Option: Ship reviewable demo documentation with public deployment explicitly unverified; Why:
- 1793194576 | plan | Victor/Victor | tasks added: HACK-027 HACK-028 HACK-029 HACK-030 | Why: backlog without PR (Plan-Channel: claims)

Global next step: available P0; else review PRs, tests, demo, rehearsal.
Why: bounded snapshot to resume without rereading history.
