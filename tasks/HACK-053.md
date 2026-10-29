# HACK-053
ID: HACK-053
State: CLAIMED
Owner: dylan-3
Branch: feat/hack-053
Worktree: /Users/dylanmartinezcastillo/Documents/Repositorios/Hackathon/Hacktoberfest-Axolutions-wt/hack-053
Worklog: worklog/WL-1793315735-dylan-3-HACK-053-hack.m6NRfB.md
Priority: P1
Paths: app/fixtures/demo/, web/src/features/project/demo.ts, web/src/features/spec/demo.ts, scripts/demo_from_recordings.py, app/tests/test_demo_fixture.py
Depends: HACK-025, HACK-051
Verify: `uv run pytest -q && uv run ruff check app scripts && ! grep -q 'example.invalid\|Placeholder' app/fixtures/demo/run.jsonl web/src/features/project/demo.ts web/src/features/spec/demo.ts && npm --prefix web run build && bash .uak/bin/design-lint && uv run python e2e/judge_path.py`
Lease-Until: 1793318435
Updated: 1793315735
Task-Base: d6fea72f0da0ff26a7b11e7a0667c0aee247bffd
Next: read how pipeline `_fixture` replays stage 3/4 and what `_record` stores for spec_ready; write the script, run it, diff run.jsonl.
PR: -
Evidence: -
Events: 1
Checkpoints: 0
Sessions: 1
Last-Checkpoint: 0
