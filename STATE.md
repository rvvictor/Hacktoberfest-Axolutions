# STATE

Phase: execution
Updated: 1793379761
AVAILABLE: HACK-061 HACK-066 HACK-067 HACK-071 
CLAIMED: -
BLOCKED: -
REVIEW: HACK-065 
INTEGRATED: (65; last 12) ... HACK-055 HACK-056 HACK-057 HACK-058 HACK-059 HACK-060 HACK-062 HACK-063 HACK-064 HACK-068 HACK-069 HACK-070 
CANCELLED: HACK-030 

Claims (first 24; status --task ID shows detail):
HACK-065 | REVIEW | victor-2 | until 1793430209

Blockers: BLOCKED tasks; use status --task ID --summary.
Current decisions (last 5):
- 1793342086 | HACK-064 | stop and ask: 3 existing tests + runs.py are outside Paths | Why: the task reverses the behaviour those tests assert; editing them without a Paths amendme
- 1793342603 | HACK-064 | recovered:true error for a skipped Miro note; getattr(board,'skipped') in stages so test doubles keep working | Why: no miro_item kind (would pollute the 
- 1793342719 | HACK-065 | server speaks only the deck it served | Why: security review: client-supplied slide = forged speech + spend
- 1793344534 | HACK-070 | recovered error = warning (no status change, no button); retryable only when payload.retry; stage_started clears error | Why: recovered errors must not lo
- 1793344905 | HACK-070 | stopped before waiting for approval: human is away | Why: user asked to leave no blockers

Global next step: available P0; else review PRs, tests, demo, rehearsal.
Why: bounded snapshot to resume without rereading history.
