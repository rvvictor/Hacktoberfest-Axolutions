# worklog/WL-1793471336-dylan-3-HACK-076-hack.CD2WQ9.md · HACK-076

## Live summary
- Done: Safari sign-in fix 06d98d3: cookies not Secure only on plain-http loopback
- Decision: Secure stays on everywhere else, incl. PUBLIC_URL https
- Why: Safari drops Secure cookies on http://localhost -> state mismatch (server log)
- Failing: none
- Commands: uv run pytest -q && uv run ruff check app
- Next: Dylan retries Google sign-in in Safari at http://localhost:8000; security review at 06d98d3

## History
- 1793471336 | CLAIMED | dylan-3 | claim; next: failing test: callback with a wrong `state` creates no session.
- 1793471658 | REVIEW | dylan-3 | done; PR https://github.com/rvvictor/Hacktoberfest-Axolutions/pull/89; evidence: Verify PASS (pytest, ruff); 14 new tests red first; Google mocked with respx; reviewer: -
- 1793471797 | REVIEW | dylan-3 | checkpoint; next: independent security review (session hit 30-subagent cap: needs a fresh session); Dylan creates Google OAuth client
- 1793475896 | REVIEW | dylan-3 | checkpoint; next: Dylan retries Google sign-in in Safari at http://localhost:8000; security review at 06d98d3
- 1793476809 | REVIEW | dylan-1 | review; approve; SHA 06d98d33285f970de1416c58380e7456a8ec5f43; reviewer dylan-1
