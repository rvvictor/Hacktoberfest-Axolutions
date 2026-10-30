# worklog/WL-1793384994-dylan-3-HACK-066-hack.LHOrkR.md · HACK-066

## Live summary
- Done: Claim created; implementation pending
- Decision: Own branch and worktree
- Why: Parallel work without touching the main checkout
- Failing: No validation run yet
- Commands: `uv run pytest -q && npm --prefix web run build && bash .uak/bin/design-lint && uv run python e2e/judge_path.py`
- Next: failing test that the demo deck uses `deck.json`, then the slide layout.

## History
- 1793384994 | CLAIMED | dylan-3 | claim; next: failing test that the demo deck uses `deck.json`, then the slide layout.
- 1793385236 | CLAIMED | dylan-3 | pending decision HACK-066-1793385236; option: demo-pitch gets the recorded research as its own passages so the recorded deck cites its own evidence; slide 0 is a cover (name from the idea, one line from the spec problem) citing the spec passage; slide sources filtered to the run's research and spec, a slide left without its sources is removed; bullets capped at 4; Why: criterion 3 forbids sources outside the run's research; keeps test_pitch.py untouched
