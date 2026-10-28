# worklog/WL-1793164791-dylan-1-HACK-017-hack.UHeRQz.md · HACK-017

## Live summary
- Done: spec UI, table, versions, client mode, approval 1
- Decision: versions from spec_ready events; client mode via ?mode=client toggle (Run has no mode)
- Why: backend lacks versions endpoint
- Failing: none
- Commands: npm --prefix web run build && design-lint
- Next: Wait for review of SHA 767da18

## History
- 1793164791 | CLAIMED | dylan-1 | claim; next: render the spec from the mock `spec_ready` event.
- 1793164945 | REVIEW | dylan-1 | done; PR https://github.com/rvvictor/Hacktoberfest-Axolutions/pull/12; evidence: build+design-lint exit 0; smoke PRODUCT_PASS; screenshots 1280/390 no page scroll; reviewer: -
- 1793164951 | REVIEW | dylan-1 | checkpoint; next: Wait for review of SHA 767da18
