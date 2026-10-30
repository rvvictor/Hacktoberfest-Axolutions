# worklog/WL-1793341858-sebas-1-HACK-064-hack.eXEMBX.md · HACK-064

## Live summary
- Done: pipeline: StageFailed, no recording replay in real runs, error event naming the provider, retry:N state + pipeline.retry(); Miro skips a note that keeps failing (BoardRun.skipped); 6 new tests pass, ruff clean
- Decision: stop and ask: 3 existing tests + runs.py are outside Paths
- Why: the task reverses the behaviour those tests assert; editing them without a Paths amendment breaks the never-edit-a-test rule
- Failing: 3 existing tests fail by design: test_pipeline.py x2, test_stages.py x1
- Commands: bash .uak/bin/q uv run pytest -q app/tests/test_live_failures.py
- Next: after Paths amendment: POST /runs/{id}/retry, rewrite the 3 tests, 'Reintentar' card in web/src/features/project

## History
- 1793341858 | CLAIMED | sebas-1 | claim; next: failing test for the replay in `_produce` (live mode), then the error event.
- 1793342086 | CLAIMED | sebas-1 | checkpoint; next: after Paths amendment: POST /runs/{id}/retry, rewrite the 3 tests, 'Reintentar' card in web/src/features/project
