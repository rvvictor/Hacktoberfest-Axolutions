# Backlog published on claims (uak plan)

Append-only; added to .uak/TASKS.md from main. Why: adding tasks never waits for a PR.
## HACK-025 · Record real fixtures: Tavily, Firecrawl and LLM with Fer's keys

- **Type:** integration
- **Priority:** P0
- **Estimate:** 45 min
- **Rubric / Spec:** C1 · `IDEA.md` §3, §10
- **Depends on:** HACK-005
- **Paths:** app/fixtures/research/, app/fixtures/llm/, scripts/record_fixtures.py
- **Freeze-Allowed:** no
- **Acceptance:**
  - Fer (the human) puts `TAVILY_API_KEY`, `FIRECRAWL_API_KEY` and `ANTHROPIC_API_KEY` in `.env` on the machine where this runs, from his editor. The agent never reads, prints or writes `.env`; it only checks that the variables are set (for example with `uv run python -c "from app.config import settings; print(bool(settings.TAVILY_API_KEY))"`).
  - `python -m app.services.research --record` records the real results for the `IDEA.md` §3 case: no `example.invalid` URL remains and every item keeps its source URL.
  - `scripts/record_fixtures.py` calls each `app/services/llm.py` function once with the real key and saves its validated output in `app/fixtures/llm/`, with `demo_data: false`.
  - The committed fixtures contain API responses only, never a key (the pre-commit secret scan passes).
- **Verify:** `uv run pytest -q app/tests/test_research.py app/tests/test_llm.py && ! grep -rq 'example.invalid' app/fixtures/research/`
- **Next step:** ask Fer to add the three keys to `.env`; then run `python -m app.services.research --record`.
## HACK-026 · Screen polish from the 1280x720 browser check: delivery, intake, spec, mobile nav, costs

- **Type:** bug
- **Priority:** P1
- **Estimate:** 45 min
- **Rubric / Spec:** C1 · `.uak/modes/sprint.md` §A stunning frontend
- **Depends on:** None
- **Paths:** web/src/features/delivery/, web/src/features/intake/, web/src/features/spec/, web/src/features/ops/, web/src/App.tsx
- **Freeze-Allowed:** yes
- **Acceptance:**
  - Delivery (`#/delivery`, demo step 4) fits 1280x720 with no vertical scroll: the quality-gate card, the remaining backlog and the approval 3 controls are all visible (today the page is 988 px tall).
  - Intake: the primary "Empezar" button explains why it is disabled (a hint or placeholder such as "Escribe o dicta tu idea"), so it never looks broken on screen.
  - Spec: the competitor table reads cleanly; the price cell no longer wraps awkwardly ("Precio simulado" / "sin precio publicado").
  - Mobile nav (390x844, `web/src/App.tsx`): the top nav no longer wraps into 3 lines or clips "Entrega"; use a horizontal scroll strip or a compact menu.
  - Costs (`#/ops`): amounts and labels are not cramped; the page fits 1280x720 or scrolls only inside a panel.
  - No regression on the wow (`#/live-board`) or the run view: both still fit 1280x720 with no scroll.
  - Only design-system tokens and `web/src/lib/ui/` components; `bash .uak/bin/design-lint` passes. Screenshots of each fixed screen at 1280x720 (and the nav at 390x844) in the PR.
- **Verify:** `npm --prefix web run build && bash .uak/bin/design-lint`
- **Next step:** run the app with `DEMO_MODE=1`, screenshot `#/delivery` at 1280x720 with Playwright (reduced motion) to reproduce the 988 px height, then fix delivery first.
## HACK-027 · Thread the run through every screen: run links, live board, delivery, pitch, intake

- **Type:** bug
- **Priority:** P0
- **Estimate:** 45 min
- **Rubric / Spec:** C1 · `IDEA.md` §1 (context continuity), §4
- **Depends on:** None
- **Uses contract:** HACK-028
- **Paths:** web/src/features/run/, web/src/features/live-board/, web/src/features/delivery/, web/src/features/intake/, web/src/features/pitch/
- **Freeze-Allowed:** yes
- **Acceptance:**
  - The run view's links to Tablero en vivo, Entrega and Pitch carry the current run (`?run=<id>`); today `web/src/features/run/index.tsx` links to bare `#/live-board`, `#/delivery` and `#/pitch`.
  - Live board, delivery and pitch read `?run=` and show that run's events and data. They fall back to the recorded demo only when no run is given, and then show the demo label.
  - Intake moves to the run view without a full page reload (hash navigation, no `location.href` reload), and the run view appears with its `run` id in under 2 s.
  - Manual check, written in the PR: create a run from intake, answer, approve gate 1, click Tablero en vivo: the board shows that run's `miro_item`/`linear_issue` events, not the replay.
- **Verify:** `npm --prefix web run build && bash .uak/bin/design-lint`
- **Next step:** in `web/src/features/run/index.tsx` build the three links with the current run id, then make `live-board/useBoardEvents.ts` subscribe to `/api/runs/{id}/events` when `?run=` is present.

## HACK-028 · Pitch and voice Q&A from the real run: deck stored, memory filled, answers with sources

- **Type:** bug
- **Priority:** P0
- **Estimate:** 60 min
- **Rubric / Spec:** C1 · `IDEA.md` §1, §4 step 6
- **Depends on:** None
- **Paths:** app/services/pipeline.py, app/services/pitch.py, app/routers/pitch.py, app/tests/test_pitch.py, app/tests/test_pipeline.py, app/tests/test_pitch_run.py
- **Freeze-Allowed:** yes
- **Acceptance:**
  - When a run reaches stage 9, `GET /api/pitch/{run_id}` returns its deck with slides (today it returns `slides: []` even after `pitch_ready`).
  - During the run, the pipeline stores the spec, every research item (with URL), the architecture and backlog decisions, and each approval comment in memory (`memory.remember`), keyed by `run_id`.
  - `POST /api/pitch/{run_id}/ask {"question":"¿Quiénes son los competidores?"}` on a finished `DEMO_MODE` run answers from those passages and returns at least one entry in `sources`; "no tengo ese dato" is kept only for questions nothing supports.
  - New test `app/tests/test_pitch_run.py`: create a run in DEMO_MODE with `DEMO_SPEED=0`, answer, approve 3 gates, then assert non-empty slides and a sourced answer.
- **Verify:** `uv run pytest -q app/tests/test_pitch.py app/tests/test_pipeline.py app/tests/test_pitch_run.py`
- **Next step:** find where the pipeline emits `pitch_ready` in `app/services/pipeline.py` and persist the deck there; then add `memory.remember` calls per stage.

## HACK-029 · End-to-end test of the judge path, run by the smoke

- **Type:** integration
- **Priority:** P1
- **Estimate:** 45 min
- **Rubric / Spec:** C1 · `.uak/modes/sprint.md` §A stunning frontend (test UI in a real browser)
- **Depends on:** HACK-027, HACK-028
- **Paths:** e2e/
- **Freeze-Allowed:** yes
- **Acceptance:**
  - `e2e/judge_path.py` (Playwright, 1280x720, reduced motion, `DEMO_MODE=1 DEMO_SPEED=0`) starts the app on a free port, goes intake → answers → approve gate 1 → live board (same run) → approve 2 and 3 → delivery → pitch, asks one question and checks the answer has a source.
  - At each step it asserts no console errors and `scrollHeight <= 720` on run, live board, delivery and pitch; it saves screenshots under `e2e/out/` (git-ignored) and exits non-zero on any failure.
  - `e2e/README.md` says how to run it in one command.
- **Verify:** `uv run python e2e/judge_path.py`
- **Next step:** copy the server start and Playwright setup from `web/src/features/pitch/check_browser.py`, then script the intake step.

## HACK-030 · Costs panel from the stored runs

- **Type:** feature
- **Priority:** P2
- **Estimate:** 30 min
- **Rubric / Spec:** C1 · proposal §8–§10
- **Depends on:** None
- **Paths:** app/routers/ops.py, app/services/costs.py, app/tests/test_ops.py, web/src/features/ops/
- **Freeze-Allowed:** yes
- **Acceptance:**
  - `GET /api/ops/runs` lists the runs in the store with their real cost per step and duration; the sample data is shown only when the store is empty, labeled demo.
  - The ops screen still fits 1280x720 (scrolling only inside a panel).
- **Verify:** `uv run pytest -q app/tests/test_ops.py && npm --prefix web run build && bash .uak/bin/design-lint`
- **Next step:** read the cost fields `app/services/store.py` saves per run, then replace the fixture in `app/services/costs.py`.

## HACK-031 · Cost wiring: services report usd via ctx.add_cost so real runs show non-zero cost in /api/ops (llm, voice, generator, research...) (follow-up of HACK-013)

- **Type:** follow-up
- **Priority:** P1
- **Depends on:** HACK-013
- **Follow-up of:** HACK-013
- **Paths:** app/routers/runs.py, app/services/pipeline.py, app/services/store.py, app/tests/test_pipeline.py
- **Freeze-Allowed:** no
- **Acceptance:**
  - Cost wiring: services report usd via ctx.add_cost so real runs show non-zero cost in /api/ops (llm, voice, generator, research...)
- **Verify:** `uv run pytest -q app/tests/test_pipeline.py`

## HACK-032 · Intake: under DEMO_MODE the screen never POSTs /api/runs/{id}/answers, so the run stalls at stage 2 (found by e2e/judge_path.py) (follow-up of HACK-014)

- **Type:** follow-up
- **Priority:** P1
- **Depends on:** HACK-014
- **Follow-up of:** HACK-014
- **Paths:** web/src/features/intake/
- **Freeze-Allowed:** no
- **Acceptance:**
  - Intake: under DEMO_MODE the screen never POSTs /api/runs/{id}/answers, so the run stalls at stage 2 (found by e2e/judge_path.py)
- **Verify:** `npm --prefix web run build && bash .uak/bin/design-lint`

## HACK-033 · Delivery: subscribe with named SSE events so the gate, prototype and quality events arrive and 'Aprobar entrega' appears (lib/sse.ts only handles unnamed events) (follow-up of HACK-018)

- **Type:** follow-up
- **Priority:** P1
- **Depends on:** HACK-018
- **Follow-up of:** HACK-018
- **Paths:** web/src/features/delivery/
- **Freeze-Allowed:** no
- **Acceptance:**
  - Delivery: subscribe with named SSE events so the gate, prototype and quality events arrive and 'Aprobar entrega' appears (lib/sse.ts only handles unnamed events)
- **Verify:** `npm --prefix web run build && bash .uak/bin/design-lint`

## HACK-034 · Run view: guard JSON.parse on the named 'error' SSE event; when the stream closes it fires JSON.parse(undefined) (follow-up of HACK-015)

- **Type:** follow-up
- **Priority:** P1
- **Depends on:** HACK-015
- **Follow-up of:** HACK-015
- **Paths:** web/src/features/run/
- **Freeze-Allowed:** no
- **Acceptance:**
  - Run view: guard JSON.parse on the named 'error' SSE event; when the stream closes it fires JSON.parse(undefined)
- **Verify:** `npm --prefix web run build && bash .uak/bin/design-lint`

## HACK-035 · n8n Cloud: read N8N_WEBHOOK_SECRET and SPEEDHACK_API_URL from $vars instead of $env (follow-up of HACK-011)

- **Type:** follow-up
- **Priority:** P1
- **Depends on:** HACK-011
- **Follow-up of:** HACK-011
- **Paths:** n8n/, app/services/outreach.py, app/fixtures/outreach/, app/tests/test_outreach.py
- **Freeze-Allowed:** no
- **Acceptance:**
  - n8n Cloud: read N8N_WEBHOOK_SECRET and SPEEDHACK_API_URL from $vars instead of $env
- **Verify:** `uv run pytest -q app/tests/test_outreach.py`

## HACK-036 · LLM provider: Gemma 4 via Gemini API (gemma-4-31b-it) selected by LLM_MODEL, Anthropic kept (follow-up of HACK-004)

- **Type:** follow-up
- **Priority:** P1
- **Depends on:** HACK-004
- **Follow-up of:** HACK-004
- **Paths:** app/services/llm.py, app/services/prompts/, app/fixtures/llm/, app/tests/test_llm.py
- **Freeze-Allowed:** no
- **Acceptance:**
  - LLM provider: Gemma 4 via Gemini API (gemma-4-31b-it) selected by LLM_MODEL, Anthropic kept
- **Verify:** `uv run pytest -q app/tests/test_llm.py`

## HACK-037 · LLM: empty or blocked Gemini response (no candidates) raises LLMOutputError, not IndexError (follow-up of HACK-036)

- **Type:** follow-up
- **Priority:** P1
- **Depends on:** HACK-036
- **Follow-up of:** HACK-036
- **Paths:** app/services/llm.py, app/services/prompts/, app/fixtures/llm/, app/tests/test_llm.py
- **Freeze-Allowed:** no
- **Acceptance:**
  - LLM: empty or blocked Gemini response (no candidates) raises LLMOutputError, not IndexError
- **Verify:** `uv run pytest -q app/tests/test_llm.py`

## HACK-038 · Hunter AI drafts use Gemma 4 via the Gemini API when LLM_MODEL selects it (follow-up of HACK-011)

- **Type:** follow-up
- **Priority:** P1
- **Depends on:** HACK-011
- **Follow-up of:** HACK-011
- **Paths:** n8n/, app/services/outreach.py, app/fixtures/outreach/, app/tests/test_outreach.py
- **Freeze-Allowed:** no
- **Acceptance:**
  - Hunter AI drafts use Gemma 4 via the Gemini API when LLM_MODEL selects it
- **Verify:** `uv run pytest -q app/tests/test_outreach.py`

## HACK-039 · Test isolation: app/tests/conftest.py blanks provider keys and forces DEMO_MODE so a developer .env never makes real API calls (follow-up of HACK-001)

- **Type:** follow-up
- **Priority:** P1
- **Depends on:** HACK-001
- **Follow-up of:** HACK-001
- **Paths:** pyproject.toml, uv.lock, .python-version, .env.example, Dockerfile, .dockerignore, render.yaml, .uak/bin/smoke-project, app/__init__.py, app/main.py, app/config.py, app/routers/__init__.py, app/services/__init__.py, app/tests/__init__.py, app/tests/test_health.py, web/package.json, web/package-lock.json, web/index.html, web/vite.config.ts, web/tsconfig.json, web/eslint.config.js, web/src/main.tsx, web/src/App.tsx, web/src/index.css, web/src/lib/api.ts, web/src/lib/sse.ts, web/src/vite-env.d.ts
- **Freeze-Allowed:** no
- **Acceptance:**
  - Test isolation: app/tests/conftest.py blanks provider keys and forces DEMO_MODE so a developer .env never makes real API calls
- **Verify:** `uv run pytest -q app/tests/test_health.py && npm --prefix web run build`

## HACK-040 · Wire the pipeline to the real services: stage adapters for stages 1-9, demo flag derived from payloads (follow-up of HACK-013)

- **Type:** follow-up
- **Priority:** P1
- **Depends on:** HACK-013
- **Follow-up of:** HACK-013
- **Paths:** app/routers/runs.py, app/services/pipeline.py, app/services/store.py, app/tests/test_pipeline.py
- **Freeze-Allowed:** no
- **Acceptance:**
  - Wire the pipeline to the real services: stage adapters for stages 1-9, demo flag derived from payloads
- **Verify:** `uv run pytest -q app/tests/test_pipeline.py`

## HACK-041 · Miro: frame height grows with its notes (3rd note was outside the 700px frame: 400 outside of parent boundaries) (follow-up of HACK-006)

- **Type:** follow-up
- **Priority:** P1
- **Depends on:** HACK-006
- **Follow-up of:** HACK-006
- **Paths:** app/services/miro.py, app/fixtures/miro/, app/tests/test_miro.py
- **Freeze-Allowed:** no
- **Acceptance:**
  - Miro: frame height grows with its notes (3rd note was outside the 700px frame: 400 outside of parent boundaries)
- **Verify:** `uv run pytest -q app/tests/test_miro.py`
