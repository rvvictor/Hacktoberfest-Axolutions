# STATE

Phase: execution
Updated: 1793340223
AVAILABLE: HACK-061 HACK-064 HACK-066 HACK-067 
CLAIMED: HACK-065 
BLOCKED: -
REVIEW: HACK-059 HACK-060 HACK-062 HACK-063 HACK-068 HACK-069 
INTEGRATED: (57; last 12) ... HACK-047 HACK-048 HACK-049 HACK-050 HACK-051 HACK-052 HACK-053 HACK-054 HACK-055 HACK-056 HACK-057 HACK-058 
CANCELLED: HACK-030 

Claims (first 24; status --task ID shows detail):
HACK-059 | REVIEW | dylan-1 | until 1793425529
HACK-060 | REVIEW | victor-3 | until 1793426486
HACK-062 | REVIEW | victor-4 | until 1793426194
HACK-063 | REVIEW | victor-1 | until 1793426534
HACK-065 | CLAIMED | victor-2 | until 1793354623
HACK-068 | REVIEW | dylan-3 | until 1793425901
HACK-069 | REVIEW | sebas-1 | until 1793426147

Blockers: BLOCKED tasks; use status --task ID --summary.
Current decisions (last 5):
- 1793339736 | HACK-069 | no browser in the Render runtime image; Dockerfile and render.yaml untouched | Why: peak ~450 MiB for the browser tree + ~110 MiB server vs 512 MB on free
- 1793340086 | HACK-060 | reuse BOARD/BACKLOG recorded data via WEB table | Why: same story as HACK-053/054
- 1793340134 | HACK-063 | deterministic junk filter instead of LLM judge | Why: stays in Paths, testable offline
- 1793340151 | deadline decision/HACK-068-1793339244/1793340144 | REVERSIBLE_AND_LOG | Option: spike calls the Lovable MCP server from this Claude Code session (Dylan's OAuth alrea
- 1793340223 | HACK-065 | POST /api/pitch/{run}/narration takes the slide in the body (deck is not deterministic), audio cached on disk per run | Why: deck() rebuilds via LLM so an

Global next step: available P0; else review PRs, tests, demo, rehearsal.
Why: bounded snapshot to resume without rereading history.
