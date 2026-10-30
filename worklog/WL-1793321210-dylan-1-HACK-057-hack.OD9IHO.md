# worklog/WL-1793321210-dylan-1-HACK-057-hack.OD9IHO.md · HACK-057

## Live summary
- Done: Claim created; implementation pending
- Decision: Own branch and worktree
- Why: Parallel work without touching the main checkout
- Failing: No validation run yet
- Commands: `bash .uak/bin/design-lint && npm --prefix web run build && bash .uak/bin/q bash .uak/bin/smoke`
- Next: after PR #57 (kit 5.8) is on main, `wt new HACK-057`; run the new `design-lint` and fix finding by finding.

## History
- 1793321210 | CLAIMED | dylan-1 | claim; next: after PR #57 (kit 5.8) is on main, `wt new HACK-057`; run the new `design-lint` and fix finding by finding.
- 1793321308 | CLAIMED | dylan-1 | pending decision HACK-057-1793321308; option: tokens.css: --sh-naranja (unused background) -> var(--sh-demo-soft), --sh-naranja-ink stays --sh-demo (AA pair already documented); index.css: drop unused Geist import and --font-sans (tokens set it to DM Sans); radii to DESIGN.md steps: logo 10->12 (sm), Más menu 16->20 (lg, card), hunter textarea 10->12 (sm), nav link 12 (sm, same); Why: kit 5.8 design-lint fails on these 8 findings and main smoke is red; no visible change except 2-4 px radii
