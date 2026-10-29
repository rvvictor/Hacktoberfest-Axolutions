# HACK-050
ID: HACK-050
State: CLAIMED
Owner: dylan-1
Branch: feat/hack-050
Worktree: /Users/dylanmartinezcastillo/Documents/Repositorios/Hackathon/Hacktoberfest-Axolutions-wt/hack-050
Worklog: worklog/WL-1793310963-dylan-1-HACK-050-hack.Pw3Ii4.md
Priority: P0
Paths: app/services/generator.py, app/services/stages.py, app/services/quality.py, app/services/llm.py, app/schemas/content.py, app/routers/prototypes.py, app/fixtures/generator/, app/tests/test_generator.py, app/tests/test_quality_generated.py, web/src/lib/types.ts, web/src/features/delivery/, app/tests/test_stages.py, e2e/
Depends: HACK-018, HACK-049
Verify: `uv run pytest -q && uv run ruff check app && npm --prefix web run build && bash .uak/bin/design-lint && uv run python e2e/judge_path.py`
Lease-Until: 1793313663
Updated: 1793310963
Task-Base: 477bd15f93b00e4a4d8eba0cf2e70b50c92e41bf
Next: spike done 2026-10-29: gemma-4-26b with maxOutputTokens 16384 produced a complete 12k-char app (finishReason STOP, ~114 s, 0 page errors, one screen per backlog item); 4096 truncates. The generator call needs its own maxOutputTokens 16384 and timeout ≥ 300 s and keeps the 500/503 retries (two 500s before success in the spike). Read stages.py `_prototype_stage`/`_quality_stage` and generator.py; add SpeedHackGenerator behind the CodeGenerator protocol.
PR: -
Evidence: -
