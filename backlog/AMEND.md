# Amended tasks (uak plan --amend)

Append-only; the last section of an ID replaces its section in the backlog. Why: Paths can grow before review.

## HACK-026 · Screen polish from the 1280x720 browser check: delivery, intake, spec, costs

- **Type:** bug
- **Priority:** P1
- **Estimate:** 45 min
- **Rubric / Spec:** C1 · `.uak/modes/sprint.md` §A stunning frontend
- **Depends on:** None
- **Paths:** web/src/features/delivery/, web/src/features/intake/, web/src/features/spec/, web/src/features/ops/
- **Freeze-Allowed:** yes
- **Acceptance:**
  - Delivery (`#/delivery`, demo step 4) fits 1280x720 with no vertical scroll: the quality-gate card, the remaining backlog and the approval 3 controls are all visible (today the page is 988 px tall).
  - Intake: the primary "Empezar" button explains why it is disabled (a hint or placeholder such as "Escribe o dicta tu idea"), so it never looks broken on screen.
  - Spec: the competitor table reads cleanly; the price cell no longer wraps awkwardly ("Precio simulado" / "sin precio publicado").
  - Costs (`#/ops`): amounts and labels are not cramped; the page fits 1280x720 or scrolls only inside a panel.
  - No regression on the wow (`#/live-board`) or the run view: both still fit 1280x720 with no scroll.
  - Only design-system tokens and `web/src/lib/ui/` components; `bash .uak/bin/design-lint` passes. Screenshots of each fixed screen at 1280x720 in the PR.
- **Verify:** `npm --prefix web run build && bash .uak/bin/design-lint`
- **Next step:** run the app with `DEMO_MODE=1`, screenshot `#/delivery` at 1280x720 with Playwright (reduced motion) to reproduce the 988 px height, then fix delivery first.
## HACK-039 · Test isolation: app/tests/conftest.py blanks provider keys and forces DEMO_MODE so a developer .env never makes real API calls (follow-up of HACK-001)

- **Type:** follow-up
- **Priority:** P1
- **Depends on:** HACK-001
- **Follow-up of:** HACK-001
- **Paths:** app/tests/conftest.py, app/tests/test_isolation.py
- **Freeze-Allowed:** yes
- **Acceptance:**
  - An autouse fixture in `app/tests/conftest.py` sets `DEMO_MODE=True`, the default Claude `LLM_MODEL`, and every provider key/ID in `app.config.settings` (plus `GEMINI_API_KEY` in `app.services.llm.gemini_env`) to `None` for every test, so a developer's real `.env` never makes a test call a real API or spend credits. Tests that need live mode keep setting it explicitly.
  - `app/tests/test_isolation.py` proves it: inside a test, every key is empty and `DEMO_MODE` is on.
  - The whole suite passes both with and without a filled `.env`, and no file outside these Paths changes.
- **Verify:** `uv run pytest -q app/tests`
## HACK-040 · Wire the pipeline to the real services: stage adapters for stages 1-9, demo flag derived from payloads (follow-up of HACK-013)

- **Type:** follow-up
- **Priority:** P1
- **Depends on:** HACK-013
- **Follow-up of:** HACK-013
- **Paths:** app/routers/runs.py, app/services/pipeline.py, app/services/store.py, app/tests/test_pipeline.py, app/services/stages.py, app/tests/test_stages.py
- **Freeze-Allowed:** yes
- **Acceptance:**
  - `app/services/stages.py` exposes `run_stage(ctx)` and `pipeline.STAGE_MODULES` maps stages 1-9 to it, so with `DEMO_MODE=false` and keys a run calls the real services (llm clarify/spec/architecture/backlog, research, Miro board, Linear backlog, prototype generator, pitch deck) instead of always replaying `app/fixtures/demo/run.jsonl`.
  - A stage counts as real only if none of its payloads carries `demo_data: true`: a service that fell back to its own recorded data (no key, DEMO_MODE, plan B) is still labeled demo.
  - Stages read what earlier stages produced from the run's events (latest attempt only after a rejection): questions + answers for the spec, research for spec and deck, architecture rebuilt from the Miro items for the backlog. A rejection comment reaches the regenerated spec/architecture.
  - Reruns never duplicate external items: Miro and Linear ids recorded in `externals` are reused.
  - Stage 8 never reports passing quality checks it did not run (no local repo of the generated app): it falls back to the labeled fixture.
  - Existing `test_pipeline.py` tests pass unchanged; `test_stages.py` covers each adapter with mocked services, the demo-flag derivation, and a full run through `TestClient`.
- **Verify:** `uv run pytest -q app/tests && bash .uak/bin/smoke`
## HACK-054 · Demo replays build the Linear issues (and Miro items) from the recorded backlog.json and architecture.json, not Issue demo N (follow-up of HACK-053)

- **Type:** follow-up
- **Priority:** P1
- **Depends on:** HACK-053
- **Follow-up of:** HACK-053
- **Paths:** app/fixtures/demo/, web/src/features/project/demo.ts, web/src/features/spec/demo.ts, scripts/demo_from_recordings.py, app/tests/test_demo_fixture.py, app/tests/test_schemas.py
- **Freeze-Allowed:** no
- **Acceptance:**
  - Demo replays build the Linear issues (and Miro items) from the recorded backlog.json and architecture.json, not Issue demo N
  - `test_schemas.py` minimum of demo linear issues follows the recorded backlog (6), by `uak decision`: the old 8 described the placeholder fixture
- **Verify:** `uv run pytest -q && uv run ruff check app scripts && ! grep -q 'example.invalid\|Placeholder' app/fixtures/demo/run.jsonl web/src/features/project/demo.ts web/src/features/spec/demo.ts && npm --prefix web run build && bash .uak/bin/design-lint && uv run python e2e/judge_path.py`
