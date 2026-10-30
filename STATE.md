# STATE

Phase: execution
Updated: 1793339890
AVAILABLE: HACK-061 HACK-064 HACK-066 HACK-067 
CLAIMED: HACK-060 HACK-063 HACK-065 
BLOCKED: -
REVIEW: HACK-059 HACK-062 HACK-068 HACK-069 
INTEGRATED: (57; last 12) ... HACK-047 HACK-048 HACK-049 HACK-050 HACK-051 HACK-052 HACK-053 HACK-054 HACK-055 HACK-056 HACK-057 HACK-058 
CANCELLED: HACK-030 

Claims (first 24; status --task ID shows detail):
HACK-059 | REVIEW | dylan-1 | until 1793425529
HACK-060 | CLAIMED | victor-3 | until 1793354241
HACK-062 | REVIEW | victor-4 | until 1793426194
HACK-063 | CLAIMED | victor-1 | until 1793354254
HACK-065 | CLAIMED | victor-2 | until 1793354248
HACK-068 | REVIEW | dylan-3 | until 1793425901
HACK-069 | REVIEW | sebas-1 | until 1793426147

Blockers: BLOCKED tasks; use status --task ID --summary.
Current decisions (last 5):
- 1793322661 | deadline decision/HACK-057-1793321308/1793322208 | REVERSIBLE_AND_LOG | Option: tokens.css: --sh-naranja (unused background) -> var(--sh-demo-soft), --sh-naranja-ink
- 1793322805 | plan | Dylan/Dylan | tasks added: HACK-058 | Why: backlog without PR (Plan-Channel: claims)
- 1793333250 | deadline lease/HACK-056/1793326124 | REQUIRES_RECOVERY | Claim kept; read the summary and use release --expired --read-summary. No work is deleted.
- 1793333270 | HACK-056 | capture.py --screenshots-only so the human re-records the video | Why: the video predates the flow; an automatic silent capture of old routes is not a pla
- 1793339736 | HACK-069 | no browser in the Render runtime image; Dockerfile and render.yaml untouched | Why: peak ~450 MiB for the browser tree + ~110 MiB server vs 512 MB on free

Global next step: available P0; else review PRs, tests, demo, rehearsal.
Why: bounded snapshot to resume without rereading history.
