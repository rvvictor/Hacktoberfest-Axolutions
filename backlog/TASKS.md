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

## HACK-042 · Design lock v2: warm 60-30-10 with blue/violet accent, 3 moments (Idea, Plan, Producto), Nielsen heuristics (follow-up of HACK-003)

- **Type:** follow-up
- **Priority:** P1
- **Depends on:** HACK-003
- **Follow-up of:** HACK-003
- **Paths:** web/DESIGN.md, web/src/styles/, web/src/lib/ui/, web/public/design-lock/
- **Freeze-Allowed:** no
- **Acceptance:**
  - Design lock v2: warm 60-30-10 with blue/violet accent, 3 moments (Idea, Plan, Producto), Nielsen heuristics
- **Verify:** `test -s web/DESIGN.md && ls web/public/design-lock/*.png`

## HACK-043 · Linear: scope issue and epic dedupe markers by run_id so a new project never reuses another project's issues (follow-up of HACK-007)

- **Type:** follow-up
- **Priority:** P1
- **Depends on:** HACK-007
- **Follow-up of:** HACK-007
- **Paths:** app/services/linear.py, app/fixtures/linear/, app/tests/test_linear.py
- **Freeze-Allowed:** no
- **Acceptance:**
  - Linear: scope issue and epic dedupe markers by run_id so a new project never reuses another project's issues
- **Verify:** `uv run pytest -q app/tests/test_linear.py`

## HACK-044 · Gemini: 4 attempts with exponential backoff (2/4/8 s); a live pitch failed after 3 consecutive 500s (follow-up of HACK-036)

- **Type:** follow-up
- **Priority:** P1
- **Depends on:** HACK-036
- **Follow-up of:** HACK-036
- **Paths:** app/services/llm.py, app/services/prompts/, app/fixtures/llm/, app/tests/test_llm.py
- **Freeze-Allowed:** no
- **Acceptance:**
  - Gemini: 4 attempts with exponential backoff (2/4/8 s); a live pitch failed after 3 consecutive 500s
- **Verify:** `uv run pytest -q app/tests/test_llm.py`
## HACK-045 · Conversation screen: one run, from the idea to the product, as a single conversation

- **Type:** feature
- **Priority:** P0
- **Estimate:** 120 min
- **Rubric / Spec:** C1 · `web/DESIGN.md` ("Conversación"), Dylan's redesign request (fewer perceived steps, warm, 60-30-10)
- **Depends on:** HACK-042
- **Paths:** web/src/features/project/
- **Freeze-Allowed:** yes
- **Acceptance:**
  - `#/project` (with `?run=ID`, or a recorded replay without it) shows the whole run as one conversation: SpeedHack messages, each result as a card (questions to answer, the plan with its sources, the Miro board, the Linear tasks, the prototype, the pitch), and one decision button per card ("Sí, sigamos" / "Cambiar algo" with a comment).
  - `Moments` (Idea · Plan · Producto) at the top replaces the 9-stage metro; the 9 stages stay reachable as "Ver detalle".
  - It reads the run's named SSE events and posts answers and approvals with the existing endpoints; no backend change.
  - Plain language: "Tu plan", "Tareas", "Revisión", "Prototipo"; demo data shows `DemoBadge`; every figure links to its source.
  - Only `web/src/lib/ui` components and `var(--sh-*)` tokens; design-lint passes; fits 1280×720 per card and works at 390 px; screenshots in the PR.
- **Verify:** `npm --prefix web run build && bash .uak/bin/design-lint`

## HACK-046 · Navigation: three entries and the conversation as the home of a run

- **Type:** feature
- **Priority:** P0
- **Estimate:** 45 min
- **Rubric / Spec:** C1 · `web/DESIGN.md` usability rule 6 (recognition over recall)
- **Depends on:** HACK-045
- **Paths:** web/src/App.tsx, web/src/main.tsx
- **Freeze-Allowed:** yes
- **Acceptance:**
  - The top bar shows the SpeedHack logo, "Nuevo proyecto", the current project (when a run is open) and a "Más" menu with Modo cliente, Cazador, Costos and the detail screens; no more than 3 visible entries.
  - Starting a project and every run link land on `#/project?run=ID`.
  - Keyboard reachable menu with visible focus; works at 390 px.
- **Verify:** `npm --prefix web run build && bash .uak/bin/design-lint`

## HACK-047 · Landing and intake in the new voice; a fresh hero capture

- **Type:** feature
- **Priority:** P1
- **Estimate:** 60 min
- **Rubric / Spec:** C1 · `web/DESIGN.md`
- **Depends on:** HACK-045
- **Paths:** web/src/features/landing/, web/public/landing/, web/src/features/intake/
- **Freeze-Allowed:** yes
- **Acceptance:**
  - The landing hero image is re-captured from the new design (no Línea 1 magenta/orange); the 9-station metro is replaced by the 3 moments.
  - Intake opens as the first turn of the conversation ("Cuéntame tu idea"), without the 9-stage metro, and hands off to `#/project?run=ID`.
  - Copy follows `web/DESIGN.md` rules; design-lint passes; screenshots at 1280 and 390 in the PR.
- **Verify:** `npm --prefix web run build && bash .uak/bin/design-lint`

## HACK-048 · Judge-path E2E follows the conversation flow: intake → #/project, questions one at a time, decisions per card (follow-up of HACK-029)

- **Type:** follow-up
- **Priority:** P1
- **Depends on:** HACK-029
- **Follow-up of:** HACK-029
- **Paths:** e2e/
- **Freeze-Allowed:** no
- **Acceptance:**
  - Judge-path E2E follows the conversation flow: intake → #/project, questions one at a time, decisions per card
- **Verify:** `uv run python e2e/judge_path.py`

## HACK-049 · ruff check e2e clean: 4 lint errors in e2e/judge_path.py (follow-up of HACK-048)

- **Type:** follow-up
- **Priority:** P1
- **Depends on:** HACK-048
- **Follow-up of:** HACK-048
- **Paths:** e2e/
- **Freeze-Allowed:** no
- **Acceptance:**
  - ruff check e2e clean: 4 lint errors in e2e/judge_path.py
- **Verify:** `uv run python e2e/judge_path.py`
## HACK-050 · SpeedHack builds the prototype itself: in-house generator, preview inside the app, real quality checks

- **Type:** feature
- **Priority:** P0
- **Estimate:** 150 min
- **Rubric / Spec:** C1 · `IDEA.md` §4 step 4
- **Depends on:** HACK-018, HACK-049
- **Paths:** app/services/generator.py, app/services/stages.py, app/services/quality.py, app/services/llm.py, app/schemas/content.py, app/routers/prototypes.py, app/fixtures/generator/, app/tests/test_generator.py, app/tests/test_quality_generated.py, web/src/lib/types.ts, web/src/features/delivery/, app/tests/test_stages.py, e2e/
- **Freeze-Allowed:** no
- **Acceptance:**
  - `generator.SpeedHackGenerator` turns the approved spec + backlog into one self-contained web app (index.html with inline CSS/JS, no external scripts or network calls) through the configured LLM (own call with maxOutputTokens 16384, timeout ≥ 300 s, 500/503 retries); the output is validated (parses as HTML, `node --check` on the inline script, size cap) with one retry, and saved under `DATA_DIR/prototypes/<run_id>/index.html`.
  - `GET /api/prototypes/{run_id}/` validates `run_id` against the run-id pattern and that the run exists (no path traversal), then serves that file with a restrictive CSP (`default-src 'none'; script-src 'unsafe-inline'; style-src 'unsafe-inline'; img-src data:`); the delivery view previews it in an `<iframe sandbox="allow-scripts">` (no `allow-same-origin`), so the user never leaves SpeedHack.
  - `_prototype_stage` uses SpeedHackGenerator first; Lovable stays as an extra "Seguir en Lovable" link (`build_url`), and the prebuilt URL / recorded page is only the fallback when generation fails or in DEMO_MODE (labeled `demo_data: true`). `Prototype.generator` accepts `speedhack` (schemas + `web/src/lib/types.ts` together).
  - `_quality_stage` runs real checks on the generated file instead of the recorded report: build (HTML parses, script passes `node --check`), lint (no external URLs, no `eval`), gitleaks-style secret scan, smoke (headless load with zero page errors); each check reports what it actually ran in `details`; a tool missing on the server (node, Playwright) reports the check as not run, never `passed`, and the secret check is not named gitleaks unless gitleaks ran. Without a generated file it keeps the current labeled fallback.
  - A recorded generator output in `app/fixtures/generator/` keeps DEMO_MODE and the tests working without keys. `test_stages.py` expectations (`generator == "lovable"`, only stage 8 demo) change by `uak decision` recorded before editing; the judge-path E2E keeps passing (delivery selectors and copy kept).
  - Prompt quality: the generation prompt includes the spec's user stories, the backlog titles and the IDEA case, asks for Spanish UI, realistic sample data marked as sample, and every backlog screen reachable from a nav.
- **Verify:** `uv run pytest -q && uv run ruff check app && npm --prefix web run build && bash .uak/bin/design-lint && uv run python e2e/judge_path.py`
- **Next step:** spike done 2026-10-29: gemma-4-26b with maxOutputTokens 16384 produced a complete 12k-char app (finishReason STOP, ~114 s, 0 page errors, one screen per backlog item); 4096 truncates. The generator call needs its own maxOutputTokens 16384 and timeout ≥ 300 s and keeps the 500/503 retries (two 500s before success in the spike). Read stages.py `_prototype_stage`/`_quality_stage` and generator.py; add SpeedHackGenerator behind the CodeGenerator protocol.
## HACK-051 · The main flow shows the prototype SpeedHack built: inline preview in #/project, and DEMO_MODE uses it too

- **Type:** feature
- **Priority:** P0
- **Estimate:** 60 min
- **Rubric / Spec:** C1 · `IDEA.md` §4 step 4
- **Depends on:** HACK-050
- **Paths:** web/src/features/project/, web/public/demo-prototype/, app/services/pipeline.py, app/tests/test_pipeline_prototype.py
- **Freeze-Allowed:** no
- **Acceptance:**
  - In `#/project`, the prototype card previews a `speedhack` prototype inline in an `<iframe sandbox="allow-scripts allow-forms allow-modals">` (no `allow-same-origin`), keeps "Abrir el prototipo" (full screen, same app) and shows "Seguir en Lovable" from `build_url`; `lovable`/`planb` prototypes keep today's links. The `secrets` check has a Spanish label ("Sin llaves expuestas" family), like the other chips.
  - With `DEMO_MODE` on (the config default, what a judge without keys runs), stages 7 and 8 run their real adapters: the recorded SpeedHack app is copied for the run (no network, `demo_data: true`) and the quality checks really run on it; every other stage keeps replaying `run.jsonl`. If either adapter raises, the stage replays the fixture as today.
  - The local replay without `?run=` (`web/src/features/project/demo.ts`) points its prototype at a static copy of the recorded app in `web/public/demo-prototype/index.html`, not at an `example.invalid` URL.
  - The judge-path E2E keeps passing.
- **Verify:** `uv run pytest -q && uv run ruff check app && npm --prefix web run build && bash .uak/bin/design-lint && uv run python e2e/judge_path.py`
- **Next step:** in pipeline `_produce`, allow stages 7-8 through `_provider` under DEMO_MODE; then the project card iframe.

## HACK-052 · Prototype iframe loads eagerly so the judge-path capture 06-prototype.png shows the app, not a blank frame (follow-up of HACK-051)

- **Type:** follow-up
- **Priority:** P1
- **Depends on:** HACK-051
- **Follow-up of:** HACK-051
- **Paths:** web/src/features/project/, web/public/demo-prototype/, app/services/pipeline.py, app/tests/test_pipeline_prototype.py
- **Freeze-Allowed:** no
- **Acceptance:**
  - Prototype iframe loads eagerly so the judge-path capture 06-prototype.png shows the app, not a blank frame
- **Verify:** `uv run pytest -q && uv run ruff check app && npm --prefix web run build && bash .uak/bin/design-lint && uv run python e2e/judge_path.py`
## HACK-053 · Demo replays show the real recorded research: no placeholder competitors or example.invalid sources

- **Type:** feature
- **Priority:** P1
- **Estimate:** 45 min
- **Rubric / Spec:** C1 · `IDEA.md` §3
- **Depends on:** HACK-025, HACK-051
- **Paths:** app/fixtures/demo/, web/src/features/project/demo.ts, web/src/features/spec/demo.ts, scripts/demo_from_recordings.py, app/tests/test_demo_fixture.py
- **Freeze-Allowed:** no
- **Acceptance:**
  - `scripts/demo_from_recordings.py` rewrites the stage-3 `research_item` events of `app/fixtures/demo/run.jsonl` from `app/fixtures/research/recorded_tavily.json` (title, URL, content) with `pricing` only when `research.extract_pricing` finds it verbatim in `recorded_firecrawl.json`, and the stage-4 `spec_ready` payload from `app/fixtures/llm/spec.json` (its sources are those URLs); every event keeps `demo_data: true`. Nothing is typed by hand and no figure is invented.
  - The stage-7 `prototype_ready` line becomes the `speedhack` recorded app (url `/api/prototypes/{run_id}/` is not valid for a replay, so the line points at `demo-prototype/index.html` as the web replay does) — or is dropped if stage 7 always runs live in DEMO_MODE (HACK-051); the choice is recorded with `uak decision`.
  - The web local replays (`web/src/features/project/demo.ts`, `web/src/features/spec/demo.ts`) use the same recorded competitors, URLs and spec, still labeled demo; no `example.invalid` and no "Placeholder" text remains in those three files.
  - A new test asserts the replay has ≥ 3 research items, all with https URLs from `recorded_tavily.json`, `demo_data: true`, and that the spec sources are a subset of them.
- **Verify:** `uv run pytest -q && uv run ruff check app scripts && ! grep -q 'example.invalid\|Placeholder' app/fixtures/demo/run.jsonl web/src/features/project/demo.ts web/src/features/spec/demo.ts && npm --prefix web run build && bash .uak/bin/design-lint && uv run python e2e/judge_path.py`
- **Next step:** read how pipeline `_fixture` replays stage 3/4 and what `_record` stores for spec_ready; write the script, run it, diff run.jsonl.

## HACK-054 · Demo replays build the Linear issues (and Miro items) from the recorded backlog.json and architecture.json, not Issue demo N (follow-up of HACK-053)

- **Type:** follow-up
- **Priority:** P1
- **Depends on:** HACK-053
- **Follow-up of:** HACK-053
- **Paths:** app/fixtures/demo/, web/src/features/project/demo.ts, web/src/features/spec/demo.ts, scripts/demo_from_recordings.py, app/tests/test_demo_fixture.py
- **Freeze-Allowed:** no
- **Acceptance:**
  - Demo replays build the Linear issues (and Miro items) from the recorded backlog.json and architecture.json, not Issue demo N
- **Verify:** `uv run pytest -q && uv run ruff check app scripts && ! grep -q 'example.invalid\|Placeholder' app/fixtures/demo/run.jsonl web/src/features/project/demo.ts web/src/features/spec/demo.ts && npm --prefix web run build && bash .uak/bin/design-lint && uv run python e2e/judge_path.py`
## HACK-057 · design-lint 5.8 clean: the 8 findings the new kit's stricter lint reports on existing screens

- **Type:** chore
- **Priority:** P0
- **Estimate:** 30 min
- **Rubric / Spec:** C1 · `web/DESIGN.md`
- **Depends on:** None
- **Paths:** web/src/App.tsx, web/src/features/hunter/index.tsx, web/src/index.css, web/src/styles/tokens.css, web/public/design-lock/3.html
- **Freeze-Allowed:** yes
- **Acceptance:** The kit 5.8 `design-lint` (PR #57) passes on main: the four `rounded-[10|12|16px]` in `App.tsx` and `hunter/index.tsx` use the radius steps of `tokens.css`; the unused Geist import and `--font-sans` in `index.css` go (tokens already set `--font-sans: var(--sh-font)`, so nothing visible changes); `--sh-naranja-ink` reads on `--sh-naranja` at 4.5:1 or more; the hex in the rejected design-lock direction 3 is a `:root` token., The two global-token touches (`index.css`, `tokens.css`) are recorded with `uak decision` before the edit; screens using `--sh-naranja-ink` (delivery, run, Panel, live-board) are captured before and after at 1280×720 and the only change is the ink contrast., Ships with `.uak-shots/HACK-057/1280.png`, `390.png` and the design critic's `VERDICT: SHIP`.
- **Verify:** `bash .uak/bin/design-lint && npm --prefix web run build && bash .uak/bin/q bash .uak/bin/smoke`
- **Next step:** after PR #57 (kit 5.8) is on main, `wt new HACK-057`; run the new `design-lint` and fix finding by finding.

## HACK-055 · The wow screen: the Miro board draws frames and notes without overlapping labels

- **Type:** bug
- **Priority:** P0
- **Estimate:** 45 min
- **Rubric / Spec:** C1 · `IDEA.md` §4 step 3 (the wow)
- **Depends on:** HACK-054, HACK-057
- **Paths:** web/src/features/live-board/, e2e/judge_path.py
- **Freeze-Allowed:** yes
- **Acceptance:** Found in the clean-clone walk at 1280×720: since HACK-054 the demo board is what `miro.BoardRun` emits (3 `frame`, 10 notes, 2 `connector`, with `w`/`h`), and `MirrorCanvas.tsx` draws every item as a fixed-size box at its (x, y) without telling frames from notes: 4 pairs of labels overlap ("Modelo de datos" under "Usuario y Roles", "Integraciones" under "Sistema de alertas…", "Pantallas" under the first note) and text spills out of its box. Live Miro runs emit the same shape, so they are probably affected too., `MirrorCanvas` draws each `frame` as a column background with its title, places each note inside its frame in a readable stack using the event's `w`/`h` (and `contract.ts` declares them), and draws connectors between the first notes of the columns. Items from the old grid shape (no `w`/`h`, no frames) still render as today., At 1280×720 with reduced motion the board and the Linear feed fit without page scroll and no two labels overlap, with the demo board and with the local replay (no `?run=`). Tokens only (`var(--sh-*)`), no hex., Ships with `.uak-shots/HACK-055/1280.png`, `390.png` and the design critic's `VERDICT: SHIP` (kit 5.8)., `e2e/judge_path.py` asserts it at the wow: after step 4, no two text labels inside `.lb-board` overlap (bounding boxes), and the wow capture is taken at 1280×720.
- **Verify:** `npm --prefix web run build && bash .uak/bin/design-lint && uv run python e2e/judge_path.py`
- **Next step:** read `web/src/features/live-board/MirrorCanvas.tsx` and `contract.ts`; run the overlap measurement from this task against the clean demo run first.

## HACK-056 · Demo kit refreshed for the conversation flow: script, rehearsal record and screenshots

- **Type:** docs
- **Priority:** P0
- **Estimate:** 40 min
- **Rubric / Spec:** C1 · `IDEA.md` §4, §8
- **Depends on:** HACK-055, HACK-057
- **Paths:** docs/demo/, README.md
- **Freeze-Allowed:** yes
- **Acceptance:** `docs/demo/script.md` is the 3-minute script for the current flow (landing → "Nuevo proyecto" → idea → three questions → plan with sources → "Ver el tablero en vivo" → tasks → prototype inline → checks → pitch Q&A) with the timing split problem 20 s → demo to the wow ≤ 90 s → how it works 40 s → impact 30 s, each part mapped to the `IDEA.md` §4 step it shows and to C1 (the official rubric is not published: no invented criteria; remap when it is). It no longer mentions the old tabs (`/#/intake`, `/#/spec`, `/#/delivery`) as the path., `docs/demo/rehearsal.md` gets a dated section for the clean clone of `main` at the merged SHA: clone, README setup, `bash .uak/bin/smoke` result, judge-path E2E result, and the measured machine time to the wow (stages 1–6 of `run.jsonl` at `DEMO_SPEED=2`), each with its real output., README screenshots and `docs/demo/screenshots/` are regenerated from the current build (`docs/demo/capture.py`) at 1280×720 with reduced motion, after HACK-055., `docs/demo/plan-b.md` says the recorded video predates the conversation flow and must be re-recorded by a human; no agent claims a video exists that it did not see.
- **Verify:** `bash .uak/bin/q bash -c 'test -s README.md && test -s docs/demo/script.md && bash .uak/bin/smoke'`
- **Next step:** copy the draft script, then run the clean-clone commands and paste their output.
