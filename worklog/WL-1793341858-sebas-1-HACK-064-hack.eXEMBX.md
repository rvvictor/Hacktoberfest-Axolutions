# worklog/WL-1793341858-sebas-1-HACK-064-hack.eXEMBX.md · HACK-064

## Live summary
- Done: backend half complete: no replay in real runs, provider-named error, retry:N + pipeline.retry, Miro skips a failing note and reports it as a recovered error, costs ignores recovered; 3 old tests rewritten; full pytest + ruff + judge_path pass
- Decision: recovered:true error for a skipped Miro note; getattr(board,'skipped') in stages so test doubles keep working
- Why: no miro_item kind (would pollute the mirror board); plain error would mark the stage failed in /ops
- Failing: -
- Commands: q uv run pytest -q; q uv run ruff check app; q uv run python e2e/judge_path.py
- Next: PR + done; HACK-070 does endpoint + card

## History
- 1793341858 | CLAIMED | sebas-1 | claim; next: failing test for the replay in `_produce` (live mode), then the error event.
- 1793342086 | CLAIMED | sebas-1 | checkpoint; next: after Paths amendment: POST /runs/{id}/retry, rewrite the 3 tests, 'Reintentar' card in web/src/features/project
- 1793342603 | CLAIMED | sebas-1 | checkpoint; next: PR + done; HACK-070 does endpoint + card
