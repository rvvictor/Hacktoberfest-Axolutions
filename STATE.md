# STATE

Phase: execution
Updated: 1793343966
AVAILABLE: HACK-061 HACK-066 HACK-067 HACK-070 HACK-071 
CLAIMED: -
BLOCKED: -
REVIEW: HACK-065 
INTEGRATED: (64; last 12) ... HACK-054 HACK-055 HACK-056 HACK-057 HACK-058 HACK-059 HACK-060 HACK-062 HACK-063 HACK-064 HACK-068 HACK-069 
CANCELLED: HACK-030 

Claims (first 24; status --task ID shows detail):
HACK-065 | REVIEW | victor-2 | until 1793430209

Blockers: BLOCKED tasks; use status --task ID --summary.
Current decisions (last 5):
- 1793340151 | deadline decision/HACK-068-1793339244/1793340144 | REVERSIBLE_AND_LOG | Option: spike calls the Lovable MCP server from this Claude Code session (Dylan's OAuth alrea
- 1793340223 | HACK-065 | POST /api/pitch/{run}/narration takes the slide in the body (deck is not deterministic), audio cached on disk per run | Why: deck() rebuilds via LLM so an
- 1793342086 | HACK-064 | stop and ask: 3 existing tests + runs.py are outside Paths | Why: the task reverses the behaviour those tests assert; editing them without a Paths amendme
- 1793342603 | HACK-064 | recovered:true error for a skipped Miro note; getattr(board,'skipped') in stages so test doubles keep working | Why: no miro_item kind (would pollute the 
- 1793342719 | HACK-065 | server speaks only the deck it served | Why: security review: client-supplied slide = forged speech + spend

Global next step: available P0; else review PRs, tests, demo, rehearsal.
Why: bounded snapshot to resume without rereading history.
