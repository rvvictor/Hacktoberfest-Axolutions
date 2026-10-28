# STATE

Phase: execution
Updated: 1793165993
AVAILABLE: HACK-024 HACK-025 
CLAIMED: HACK-006 HACK-007 HACK-008 HACK-011 HACK-019 
BLOCKED: -
REVIEW: HACK-005 HACK-009 HACK-013 HACK-018 HACK-021 HACK-022 HACK-023 
INTEGRATED: HACK-001 HACK-002 HACK-003 HACK-004 HACK-010 HACK-012 HACK-014 HACK-015 HACK-016 HACK-017 HACK-020 
CANCELLED: -

Claims (first 24; status --task ID shows detail):
HACK-005 | REVIEW | victor-3 | until 1793180222
HACK-006 | CLAIMED | fer-1 | until 1793165698
HACK-007 | CLAIMED | fer-2 | until 1793162595
HACK-008 | CLAIMED | sebas-2 | until 1793167687
HACK-009 | REVIEW | victor-1 | until 1793179995
HACK-011 | CLAIMED | sebas-1 | until 1793167798
HACK-013 | REVIEW | victor-1 | until 1793179939
HACK-018 | REVIEW | jabi-2 | until 1793180172
HACK-019 | CLAIMED | jabi-1 | until 1793167815
HACK-021 | REVIEW | victor-2 | until 1793179943
HACK-022 | REVIEW | victor-2 | until 1793180065
HACK-023 | REVIEW | dylan-1 | until 1793180053

Blockers: BLOCKED tasks; use status --task ID --summary.
Current decisions (last 5):
- 1793165653 | HACK-023 | no prices (none in IDEA §10) | Why: no source
- 1793165665 | HACK-022 | Read HACK-013 sqlite tables directly; units derived from usd via estimated price table | Why: HACK-013 only stores usd per step and is unmerged
- 1793165665 | HACK-005 | fixtures simulated (demo_data, example.invalid) until keys exist | Why: no TAVILY/FIRECRAWL keys
- 1793165764 | deadline lease/HACK-006/1793165698 | REQUIRES_RECOVERY | Claim kept; read the summary and use release --expired --read-summary. No work is deleted.
- 1793165941 | plan | Victor/Victor | tasks added: HACK-025 | Why: backlog without PR (Plan-Channel: claims)

Global next step: available P0; else review PRs, tests, demo, rehearsal.
Why: bounded snapshot to resume without rereading history.
