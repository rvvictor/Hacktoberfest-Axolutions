# worklog/WL-1793339213-dylan-3-HACK-068-hack.r18F5z.md · HACK-068

## Live summary
- Done: Claim created; implementation pending
- Decision: Own branch and worktree
- Why: Parallel work without touching the main checkout
- Failing: No validation run yet
- Commands: `test -s docs/specs/002-real-product/spike-lovable.md && uv run ruff check scripts`
- Next: read the MCP server docs; Dylan authorizes the OAuth login and the credit spend before the first call.

## History
- 1793339213 | CLAIMED | dylan-3 | claim; next: read the MCP server docs; Dylan authorizes the OAuth login and the credit spend before the first call.
- 1793339244 | CLAIMED | dylan-3 | pending decision HACK-068-1793339244; option: spike calls the Lovable MCP server from this Claude Code session (Dylan's OAuth already done in the client); scripts/spikes/lovable_mcp.py records the calls and whether a server-side client can do the same OAuth; Why: measure create_project, preview/deploy URLs, time and credits first; a server OAuth client is a finding, not a prerequisite
