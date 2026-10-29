# worklog/WL-1793310963-dylan-1-HACK-050-hack.Pw3Ii4.md · HACK-050

## Live summary
- Done: Claim created; implementation pending
- Decision: Own branch and worktree
- Why: Parallel work without touching the main checkout
- Failing: No validation run yet
- Commands: `uv run pytest -q && uv run ruff check app && npm --prefix web run build && bash .uak/bin/design-lint && uv run python e2e/judge_path.py`
- Next: spike done 2026-10-29: gemma-4-26b with maxOutputTokens 16384 produced a complete 12k-char app (finishReason STOP, ~114 s, 0 page errors, one screen per backlog item); 4096 truncates. The generator call needs its own maxOutputTokens 16384 and timeout ≥ 300 s and keeps the 500/503 retries (two 500s before success in the spike). Read stages.py `_prototype_stage`/`_quality_stage` and generator.py; add SpeedHackGenerator behind the CodeGenerator protocol.

## History
- 1793310963 | CLAIMED | dylan-1 | claim; next: spike done 2026-10-29: gemma-4-26b with maxOutputTokens 16384 produced a complete 12k-char app (finishReason STOP, ~114 s, 0 page errors, one screen per backlog item); 4096 truncates. The generator call needs its own maxOutputTokens 16384 and timeout ≥ 300 s and keeps the 500/503 retries (two 500s before success in the spike). Read stages.py `_prototype_stage`/`_quality_stage` and generator.py; add SpeedHackGenerator behind the CodeGenerator protocol.
- 1793311092 | CLAIMED | dylan-1 | pending decision HACK-050-1793311092; option: test_stages live_services also stubs the new SpeedHack generator; the live-run test then expects generator speedhack with a /api/prototypes/ url and stage 8 real (no demo stage left) instead of lovable + stage 8 demo; Why: the stage now generates the app itself and quality checks the generated file; unstubbed, the test would call the real LLM wherever .env has keys
- 1793311410 | CLAIMED | dylan-1 | pending decision HACK-050-1793311410; option: test_prototype_previews_the_prebuilt_app... now makes SpeedHack generation fail first, since the prebuilt app is only the fallback; Why: acceptance: prebuilt URL / recorded page only when generation fails or in DEMO_MODE
