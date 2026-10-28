# HACK-027
ID: HACK-027
State: CLAIMED
Owner: victor-2
Branch: feat/hack-027
Worktree: /Users/victor/Documents/Proyectos/Hacktoberfest-Axolutions-wt/hack-027
Worklog: worklog/WL-1793194597-victor-2-HACK-027-hack.vrlVOK.md
Priority: P0
Paths: web/src/features/run/, web/src/features/live-board/, web/src/features/delivery/, web/src/features/intake/, web/src/features/pitch/
Depends: None
Verify: `npm --prefix web run build && bash .uak/bin/design-lint`
Lease-Until: 1793197297
Updated: 1793194597
Task-Base: 8ea0211a065f113b370633897abcad824b16f449
Next: in `web/src/features/run/index.tsx` build the three links with the current run id, then make `live-board/useBoardEvents.ts` subscribe to `/api/runs/{id}/events` when `?run=` is present.
PR: -
Evidence: -
Events: 1
Checkpoints: 0
Sessions: 1
Last-Checkpoint: 0
