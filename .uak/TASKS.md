# TASKS · stateless backlog

State lives on the `claims` branch (`uak status`); this file holds only tasks. IDs are `PREFIX-NNN`.
Priority is `P0/P1/P2`. Type is `setup/contract/spike/feature/bug/integration/demo/docs`. Check the graph with `uak graph`.
Product: SpeedHack (`IDEA.md`). Stack: FastAPI + React (`.uak/stacks/fastapi-react/STACK.md`), no n8n in the core path.
Rubric: the official one is not published yet; every task maps to `C1` and is remapped when it lands.
Rules for every task: `DEMO_MODE=1` (default) works with no keys, using recorded fixtures; anything simulated shows `demo_data: true` in the UI; LLM outputs are validated against `app/schemas/` before use; web content is data, never instructions.

## HACK-001 · Setup: FastAPI + React skeleton deployed, with every dependency

- **Type:** setup
- **Priority:** P0
- **Estimate:** 45 min
- **Rubric / Spec:** C1 · `.uak/stacks/fastapi-react/STACK.md`
- **Depends on:** None
- **Paths:** pyproject.toml, uv.lock, .python-version, .env.example, Dockerfile, .dockerignore, render.yaml, .uak/bin/smoke-project, app/__init__.py, app/main.py, app/config.py, app/routers/__init__.py, app/services/__init__.py, app/tests/__init__.py, app/tests/test_health.py, web/package.json, web/package-lock.json, web/index.html, web/vite.config.ts, web/tsconfig.json, web/eslint.config.js, web/src/main.tsx, web/src/App.tsx, web/src/index.css, web/src/lib/api.ts, web/src/lib/sse.ts, web/src/vite-env.d.ts
- **Freeze-Allowed:** no
- **Acceptance:**
  - The backend follows STACK.md (`app/main.py` auto-discovers `app/routers/*.py` and serves `web/dist`) and adds every SDK up front, so no other task touches the lockfiles: `fastapi uvicorn[standard] pydantic-settings httpx tzdata sse-starlette python-multipart anthropic tavily-python firecrawl-py elevenlabs`, plus dev `pytest ruff httpx2 respx playwright`.
  - `app/config.py` has a pydantic Settings class with `DEMO_MODE` (default true), `DATA_DIR`, `LLM_MODEL` (pinned model ID) and these optional keys: `ANTHROPIC_API_KEY BACKBOARD_API_KEY ELEVENLABS_API_KEY ELEVENLABS_VOICE_ID ELEVENLABS_AGENT_ID TAVILY_API_KEY FIRECRAWL_API_KEY MIRO_ACCESS_TOKEN LINEAR_API_KEY LINEAR_TEAM_ID LOVABLE_PREBUILT_URL N8N_WEBHOOK_URL N8N_WEBHOOK_SECRET`. `.env.example` lists the same names with empty values.
  - The web app uses Vite, React, TS, Tailwind v4, Motion and `@elevenlabs/react`. `App.tsx` is a hash router built from `import.meta.glob("./features/*/index.tsx")`: each feature exports `default`, `path`, `label` and `order`, and the nav comes from them. `main.tsx` also eager-globs `./styles/*.css` (owned by HACK-003), so the build passes before the design lock. `lib/sse.ts` exports a typed `subscribe(url, onEvent)` helper.
  - `bash .uak/bin/uak deploy --write` creates the Dockerfile and `render.yaml`. `uak init-smoke` uses the STACK.md command, so `bash .uak/bin/smoke` exits 0.
- **Verify:** `uv run pytest -q app/tests/test_health.py && npm --prefix web run build`
- **Next step:** follow `.uak/stacks/fastapi-react/STACK.md` §Backend setup, then §Frontend setup.

## HACK-002 · Contract: spec, run and stage-event schemas, a full recorded demo run, TS types

- **Type:** contract
- **Priority:** P0
- **Estimate:** 45 min
- **Rubric / Spec:** C1 · `IDEA.md` §6
- **Depends on:** None
- **Paths:** app/schemas/, app/fixtures/demo/, app/tests/test_schemas.py, web/src/lib/types.ts, web/src/lib/mock.ts
- **Freeze-Allowed:** no
- **Acceptance:**
  - `app/schemas/` holds Pydantic models for every entity in `IDEA.md` §6: Project, Run, StageEvent, Spec, ResearchItem, Architecture (+ MiroItem), BacklogItem, Prototype, QualityReport, Pitch, Prospect. Every response that can be simulated carries `demo_data: bool`.
  - `StageEvent.type` is an enum covering the whole flow: `stage_started`, `stage_done`, `question`, `research_item`, `spec_ready`, `approval_required`, `approval_given`, `approval_rejected`, `miro_item`, `linear_issue`, `prototype_ready`, `quality_check`, `pitch_ready`, `error`.
  - `app/fixtures/demo/run.jsonl` is one complete run of the `IDEA.md` §3 case: 9 stages, 3 approvals, at least 12 `miro_item` and 8 `linear_issue` events, with relative timestamps for replay. Research items are placeholders marked `demo_data: true` until HACK-005 records real ones.
  - `web/src/lib/types.ts` mirrors the schemas; `web/src/lib/mock.ts` replays `run.jsonl` with the same timing.
  - The test validates every fixture line against the schemas.
- **Verify:** `uv run pytest -q app/tests/test_schemas.py`
- **Next step:** write `app/schemas/run.py` (Run, StageEvent) first, then announce it with `uak msg all --kind contract`.

## HACK-003 · Design lock: three directions, the human picks one, tokens frozen

- **Type:** setup
- **Priority:** P0
- **Estimate:** 45 min
- **Rubric / Spec:** C1 · `.uak/modes/sprint.md` §A stunning frontend
- **Depends on:** None
- **Paths:** web/DESIGN.md, web/src/styles/, web/src/lib/ui/, web/public/design-lock/
- **Freeze-Allowed:** no
- **Acceptance:**
  - Run with `/uak-design-lock`: three directions with screenshots at 1280×720 and 390×844 of the wow screen (Miro + Linear filling in side by side) and the run timeline; the human picks one.
  - `web/DESIGN.md` is frozen with the pick; tokens live in `web/src/styles/tokens.css`; base components (Button, Card, Badge with a `demo_data` variant, Stepper, Panel) live in `web/src/lib/ui/`.
- **Verify:** `test -s web/DESIGN.md && ls web/public/design-lock/*.png`
- **Next step:** run `/uak-design-lock` with `IDEA.md` §0 and §4.

## HACK-004 · LLM service: clarification, spec, architecture, backlog and deck with validated output

- **Type:** feature
- **Priority:** P0
- **Estimate:** 60 min
- **Rubric / Spec:** C1 · `IDEA.md` §5, §7
- **Depends on:** None
- **Uses contract:** HACK-002
- **Paths:** app/services/llm.py, app/services/prompts/, app/fixtures/llm/, app/tests/test_llm.py
- **Freeze-Allowed:** no
- **Acceptance:**
  - `clarify(idea, mode)` returns 3–5 questions: technical ones in `dev` mode, plain-language ones in `client` mode.
  - `build_spec`, `build_architecture`, `build_backlog`, `build_deck` and `answer(question, passages)` return models from `app/schemas/`. Invalid model output is retried once, then raises a typed error; it never writes partial data.
  - `build_spec` cites only the research URLs it received and never writes a figure that is not in them.
  - With `DEMO_MODE=1` or no key, each function returns its recorded fixture; one real response per function is recorded in `app/fixtures/llm/`.
- **Verify:** `uv run pytest -q app/tests/test_llm.py`
- **Next step:** spike `settings.LLM_MODEL` with one real call and record it; then write `clarify`.

## HACK-005 · Research service: Tavily + Firecrawl, cached, every figure with its URL

- **Type:** feature
- **Priority:** P0
- **Estimate:** 45 min
- **Rubric / Spec:** C1 · `IDEA.md` §3, §10
- **Depends on:** None
- **Uses contract:** HACK-002
- **Paths:** app/services/research.py, app/fixtures/research/, app/tests/test_research.py
- **Freeze-Allowed:** no
- **Acceptance:**
  - `research(spec_draft, mode)` returns at least 3 ResearchItem (competitor, pricing, features, url, fetched_at) for the demo case. `dev` mode adds current docs for the requested stack (for example Supabase Auth).
  - Results are cached per query and per URL under `DATA_DIR`, and there is a per-run credit cap.
  - The real results for the `IDEA.md` §3 case are recorded in `app/fixtures/research/`; nothing is typed by hand. An item without a URL is dropped.
- **Verify:** `uv run pytest -q app/tests/test_research.py`
- **Next step:** spike one Tavily search for "corporate expense management software pricing Mexico" and record it.

## HACK-006 · Miro service: build the architecture board item by item

- **Type:** feature
- **Priority:** P0
- **Estimate:** 60 min
- **Rubric / Spec:** C1 · `IDEA.md` §4 step 3 (wow)
- **Depends on:** None
- **Uses contract:** HACK-002
- **Paths:** app/services/miro.py, app/fixtures/miro/, app/tests/test_miro.py
- **Freeze-Allowed:** no
- **Acceptance:**
  - `build_board(architecture)` creates a board (REST API v2) with frames for screens, data model and integrations, plus connectors. It yields one `miro_item` event per created item, so the UI can draw it live, and returns the board's live-embed URL.
  - It retries with backoff on 429 and stores external IDs, so a retry never duplicates items.
  - With `DEMO_MODE=1` it yields the recorded items, with x/y/w/h and color, at the recorded pace, so the UI can draw a mirror of the board.
- **Verify:** `uv run pytest -q app/tests/test_miro.py`
- **Next step:** spike creating one board with one sticky note and record the response.

## HACK-007 · Linear service: epics and issues with acceptance criteria, idempotent

- **Type:** feature
- **Priority:** P0
- **Estimate:** 45 min
- **Rubric / Spec:** C1 · `IDEA.md` §4 step 3 (wow)
- **Depends on:** None
- **Uses contract:** HACK-002
- **Paths:** app/services/linear.py, app/fixtures/linear/, app/tests/test_linear.py
- **Freeze-Allowed:** no
- **Acceptance:**
  - `create_backlog(items)` creates epics (projects or parent issues) and 5–8 issues with acceptance criteria in `LINEAR_TEAM_ID`. It yields one `linear_issue` event per issue, with its identifier and URL.
  - Idempotency: an `external_id` marker in each description means a re-run finds existing issues instead of duplicating them.
  - `DEMO_MODE=1` replays the recorded issues.
- **Verify:** `uv run pytest -q app/tests/test_linear.py`
- **Next step:** spike the GraphQL `issueCreate` mutation with one issue and record it.

## HACK-008 · Voice service: dictation and spoken answers with ElevenLabs

- **Type:** feature
- **Priority:** P0
- **Estimate:** 60 min
- **Rubric / Spec:** C1 · `IDEA.md` §4 steps 1 and 6 · track ElevenLabs
- **Depends on:** None
- **Uses contract:** HACK-002
- **Paths:** app/services/voice.py, app/routers/voice.py, app/fixtures/voice/, app/tests/test_voice.py
- **Freeze-Allowed:** no
- **Acceptance:**
  - `POST /api/voice/stt` (multipart audio) returns `{text}`; `POST /api/voice/tts` `{text}` returns `audio/mpeg`.
  - If the Conversational AI agent is used, `GET /api/voice/session` returns a signed URL, so the key never reaches the browser.
  - Every spoken session starts with a sentence saying the voice is an AI.
  - `DEMO_MODE=1` returns a recorded transcript and recorded audio from `app/fixtures/voice/`.
- **Verify:** `uv run pytest -q app/tests/test_voice.py`
- **Next step:** spike one TTS call with `ELEVENLABS_VOICE_ID` and save the mp3 as a fixture.

## HACK-009 · Memory service: Backboard as the project's thread of context

- **Type:** feature
- **Priority:** P0
- **Estimate:** 45 min
- **Rubric / Spec:** C1 · `IDEA.md` §1, §5 · track Backboard
- **Depends on:** None
- **Uses contract:** HACK-002
- **Paths:** app/services/memory.py, app/fixtures/memory/, app/tests/test_memory.py
- **Freeze-Allowed:** no
- **Acceptance:**
  - `remember(run_id, kind, text, source)` stores the spec, decisions, research and approval comments; `recall(run_id, query, k)` returns passages with their source (stage, URL or decision).
  - Backboard is a cache: the spec of record stays in our store (HACK-013). Without a key, a local keyword index gives the same interface.
  - One real remember/recall round trip is recorded in `app/fixtures/memory/`.
- **Verify:** `uv run pytest -q app/tests/test_memory.py`
- **Next step:** spike the Backboard API (create assistant/thread, add memory, query) from its docs and record it.

## HACK-010 · Prototype generator: a CodeGenerator interface with Lovable Build-with-URL and a plan B

- **Type:** feature
- **Priority:** P0
- **Estimate:** 45 min
- **Rubric / Spec:** C1 · `IDEA.md` §4 step 4, §10 (Lovable docs)
- **Depends on:** None
- **Uses contract:** HACK-002
- **Paths:** app/services/generator.py, app/fixtures/generator/, app/tests/test_generator.py
- **Freeze-Allowed:** no
- **Acceptance:**
  - A `CodeGenerator` protocol has two implementations. `LovableGenerator` builds the master prompt from the spec and backlog and returns the Build-with-URL link, following the format in docs.lovable.dev/integrations/lovable-api. `PlanBGenerator` returns `LOVABLE_PREBUILT_URL` or a recorded app.
  - Both return a `Prototype`. The plan B result is labeled `demo_data: true`.
  - The master prompt never includes raw web content, only validated spec fields.
- **Verify:** `uv run pytest -q app/tests/test_generator.py`
- **Next step:** read the Lovable API docs, then write `LovableGenerator.build_url(spec)`.

## HACK-011 · n8n outreach flow: AI draft → human approval → send with opt-out

- **Type:** feature
- **Priority:** P1
- **Estimate:** 60 min
- **Rubric / Spec:** C1 · `IDEA.md` §2, §9 · track n8n
- **Depends on:** None
- **Uses contract:** HACK-002
- **Paths:** n8n/, app/services/outreach.py, app/fixtures/outreach/, app/tests/test_outreach.py
- **Freeze-Allowed:** no
- **Acceptance:**
  - `n8n/workflows/hunter-outreach.json` is an exported workflow: an HMAC-signed webhook, a wait for approval, a mock send (no real email or WhatsApp), then a callback to `/api/hunter/...`. `n8n/README.md` explains how to import it.
  - `outreach.py` signs and calls `N8N_WEBHOOK_URL`. Without it, it runs the same steps in-process, so the demo never depends on n8n being up.
  - It never sends without `approved_by`; every message includes an opt-out line; a prospect with `opt_out` is skipped.
- **Verify:** `uv run pytest -q app/tests/test_outreach.py`
- **Next step:** write the in-process flow in `outreach.py`, then mirror it in n8n. Hosting n8n (Cloud or Docker) needs a human's OK.

## HACK-012 · Quality gate for the generated app: build, secrets, RLS and smoke

- **Type:** feature
- **Priority:** P1
- **Estimate:** 60 min
- **Rubric / Spec:** C1 · `IDEA.md` §4 step 4
- **Depends on:** None
- **Uses contract:** HACK-002
- **Paths:** quality/, app/services/quality.py, app/fixtures/quality/, app/tests/test_quality.py
- **Freeze-Allowed:** no
- **Acceptance:**
  - `quality/generated-repo-ci.yml` is a GitHub Actions template for the generated repo: build, lint, gitleaks, `npm audit`, the RLS check and a Playwright smoke.
  - `quality/check_rls.py` parses Supabase migrations and fails when a table lacks `enable row level security` or has only a trivial `using (true)` policy.
  - `quality.run(repo_path)` returns a QualityReport with each check's status and details. Fixtures include one repo that passes and one that fails RLS.
- **Verify:** `uv run pytest -q app/tests/test_quality.py`
- **Next step:** write `check_rls.py` against `app/fixtures/quality/bad/supabase/migrations/`.

## HACK-013 · Pipeline: 9 stages, 3 approvals, SSE events and a SQLite store

- **Type:** feature
- **Priority:** P0
- **Estimate:** 60 min
- **Rubric / Spec:** C1 · `IDEA.md` §4, §5
- **Depends on:** None
- **Uses contract:** HACK-002, HACK-004, HACK-005, HACK-006, HACK-007, HACK-009, HACK-010, HACK-012
- **Paths:** app/routers/runs.py, app/services/pipeline.py, app/services/store.py, app/tests/test_pipeline.py
- **Freeze-Allowed:** no
- **Acceptance:**
  - `POST /api/projects` `{mode, idea}` creates a run. `POST /api/runs/{id}/answers` continues it. `POST /api/runs/{id}/approvals/{1|2|3}` `{approved, comment}` advances it, or goes back one stage with the comment.
  - `GET /api/runs/{id}` returns the state. `GET /api/runs/{id}/events` streams StageEvents over SSE, replaying past events first.
  - The pipeline calls each service through a registry. A missing module or a failing provider falls back to `app/fixtures/demo/run.jsonl` and emits the event with `demo_data: true`, so the run always finishes.
  - The spec is versioned in SQLite under `DATA_DIR` and is the source of truth. External IDs are stored per stage, so stages are idempotent. Cost per step is recorded.
- **Verify:** `uv run pytest -q app/tests/test_pipeline.py`
- **Next step:** write `store.py`, then a pipeline that replays `run.jsonl`; swap in real services one by one.

## HACK-014 · Intake screen: mode switch, dictation and clarifying questions

- **Type:** feature
- **Priority:** P0
- **Estimate:** 45 min
- **Rubric / Spec:** C1 · `IDEA.md` §4 step 1
- **Depends on:** HACK-003
- **Uses contract:** HACK-002, HACK-008, HACK-013
- **Paths:** web/src/features/intake/
- **Freeze-Allowed:** no
- **Acceptance:**
  - A Desarrollador / Cliente switch, a textarea and a mic button: recording sends audio to `/api/voice/stt` and shows the transcript; Desarrollador mode can pin a stack.
  - Submit creates the run, shows the clarifying questions and sends the answers, then routes to the run view.
  - It has empty, loading, error and `demo_data` states. It works with the keyboard.
- **Verify:** `npm --prefix web run build && bash .uak/bin/design-lint`
- **Next step:** build the form on `web/src/lib/mock.ts`, then switch to `/api/projects`.

## HACK-015 · Run view: a live 9-stage timeline with the 3 approval gates

- **Type:** feature
- **Priority:** P0
- **Estimate:** 60 min
- **Rubric / Spec:** C1 · `IDEA.md` §4 steps 2–4
- **Depends on:** HACK-003
- **Uses contract:** HACK-002, HACK-013
- **Paths:** web/src/features/run/
- **Freeze-Allowed:** no
- **Acceptance:**
  - A stepper with the 9 stages fed by SSE (`lib/sse.ts`); each stage shows its status and time.
  - At each approval gate, an "Aprobar / Pedir cambios" panel with a comment box posts to `/approvals/{n}`. A rejection shows the run going back one stage.
  - Links to the spec, live board, delivery and pitch views for this `run`.
- **Verify:** `npm --prefix web run build && bash .uak/bin/design-lint`
- **Next step:** render the stepper from the mock replay.

## HACK-016 · WOW: Miro and Linear filling in live, side by side

- **Type:** feature
- **Priority:** P0
- **Estimate:** 60 min
- **Rubric / Spec:** C1 · `IDEA.md` §4 step 3
- **Depends on:** HACK-003
- **Uses contract:** HACK-002, HACK-006, HACK-007, HACK-013
- **Paths:** web/src/features/live-board/
- **Freeze-Allowed:** no
- **Acceptance:**
  - Left: the Miro live embed when there is a board URL, and always a mirror canvas that draws each `miro_item` (position, size, color) as it arrives. Right: Linear issues appear one by one with their identifier, epic, acceptance criteria and a link.
  - It fits in 1280×720 without scrolling and shows a counter (items and issues created). Motion respects `prefers-reduced-motion`.
  - With the mock, the full wow plays in 45 s or less and is labeled `demo_data`.
- **Verify:** `npm --prefix web run build && bash .uak/bin/design-lint`
- **Next step:** build the mirror canvas on the `miro_item` events from `lib/mock.ts`.

## HACK-017 · Spec and research review: approval 1 with cited sources

- **Type:** feature
- **Priority:** P0
- **Estimate:** 45 min
- **Rubric / Spec:** C1 · `IDEA.md` §4 step 2
- **Depends on:** HACK-003
- **Uses contract:** HACK-002, HACK-013
- **Paths:** web/src/features/spec/
- **Freeze-Allowed:** no
- **Acceptance:**
  - Shows the spec (problem, users, MVP features, assumptions) and a competitor table (pricing, features) where every figure links to its URL. There is a version selector.
  - Client mode shows a plain-language summary instead of the technical spec.
- **Verify:** `npm --prefix web run build && bash .uak/bin/design-lint`
- **Next step:** render the spec from the mock `spec_ready` event.

## HACK-018 · Delivery: the prototype and the quality report (approval 3)

- **Type:** feature
- **Priority:** P0
- **Estimate:** 45 min
- **Rubric / Spec:** C1 · `IDEA.md` §4 step 4
- **Depends on:** HACK-003
- **Uses contract:** HACK-002, HACK-010, HACK-012, HACK-013
- **Paths:** web/src/features/delivery/
- **Freeze-Allowed:** no
- **Acceptance:**
  - Shows the prototype (an iframe or preview with an "Abrir en Lovable" button), the generator used (Lovable or plan B) and the repo link.
  - Shows each quality check with pass/fail and details, with failures visible; the remaining backlog; and the approval 3 controls.
- **Verify:** `npm --prefix web run build && bash .uak/bin/design-lint`
- **Next step:** render the `quality_check` events from the mock.

## HACK-019 · Pitch room: generated deck and voice Q&A grounded in the project's memory

- **Type:** feature
- **Priority:** P0
- **Estimate:** 60 min
- **Rubric / Spec:** C1 · `IDEA.md` §4 step 6
- **Depends on:** HACK-003
- **Uses contract:** HACK-002, HACK-004, HACK-008, HACK-009
- **Paths:** app/routers/pitch.py, app/services/pitch.py, app/tests/test_pitch.py, web/src/features/pitch/
- **Freeze-Allowed:** no
- **Acceptance:**
  - `GET /api/pitch/{run_id}` returns the deck. `POST /api/pitch/{run_id}/ask` `{question}` recalls passages from memory, answers through `llm.answer` and returns `{answer, sources[]}`. A question with no supporting passage gets "no tengo ese dato" instead of a guess.
  - The UI shows the slides (exportable with print to PDF), a push-to-talk button (STT → ask → TTS) and the sources under each answer. The first answer says it is an AI.
- **Verify:** `uv run pytest -q app/tests/test_pitch.py && npm --prefix web run build && bash .uak/bin/design-lint`
- **Next step:** write `pitch.ask` on the memory and LLM fixtures.

## HACK-020 · Client mode: the barbershop journey in plain language

- **Type:** feature
- **Priority:** P1
- **Estimate:** 60 min
- **Rubric / Spec:** C1 · `IDEA.md` §2, §3
- **Depends on:** HACK-003
- **Uses contract:** HACK-002, HACK-008, HACK-013
- **Paths:** app/routers/client.py, app/fixtures/client/, app/tests/test_client.py, web/src/features/client/
- **Freeze-Allowed:** no
- **Acceptance:**
  - Walks the fictional barbershop (`demo_data: true`) through the same engine: 3–5 simple questions, a plain summary, a screen map image, a progress bar instead of Linear, a mock WhatsApp preview (opt-in shown), the published app link and a 2-minute audio guide.
- **Verify:** `uv run pytest -q app/tests/test_client.py && npm --prefix web run build && bash .uak/bin/design-lint`
- **Next step:** write the barbershop fixture and `GET /api/client/demo`.

## HACK-021 · Hunter console: prospects with consent and human-approved outreach

- **Type:** feature
- **Priority:** P1
- **Estimate:** 60 min
- **Rubric / Spec:** C1 · `IDEA.md` §2, §9 · track n8n
- **Depends on:** HACK-003
- **Uses contract:** HACK-002, HACK-004, HACK-011
- **Paths:** app/routers/hunter.py, app/fixtures/hunter/, app/tests/test_hunter.py, web/src/features/hunter/
- **Freeze-Allowed:** no
- **Acceptance:**
  - `GET /api/hunter/prospects` returns fictional businesses with public info only (`demo_data: true`).
  - Draft: the AI writes a message, the operator edits and approves it, and the n8n flow runs (or its in-process fallback). The status shows draft → approved → sent (mock) → replied.
  - The UI shows the rules: no cold calls, opt-out, 30-day retention, a call only when the business asks.
- **Verify:** `uv run pytest -q app/tests/test_hunter.py && npm --prefix web run build && bash .uak/bin/design-lint`
- **Next step:** write the prospects fixture and the router on the `outreach.py` contract.

## HACK-022 · Costs and observability panel: run_id, cost per step and status per stage

- **Type:** feature
- **Priority:** P2
- **Estimate:** 45 min
- **Rubric / Spec:** C1 · proposal §8–§10
- **Depends on:** HACK-003
- **Uses contract:** HACK-002, HACK-013
- **Paths:** app/routers/ops.py, app/services/costs.py, app/tests/test_ops.py, web/src/features/ops/
- **Freeze-Allowed:** no
- **Acceptance:**
  - `GET /api/ops/runs` lists runs with duration and cost per step (tokens, credits, voice minutes). Prices come from a config table with a source URL, or are labeled estimated.
  - The UI shows the cost per project against the plan budget, and failures per stage.
- **Verify:** `uv run pytest -q app/tests/test_ops.py && npm --prefix web run build && bash .uak/bin/design-lint`
- **Next step:** read the cost-per-step fields that HACK-013 stores.

## HACK-023 · Landing: the idea in 5 seconds, real screens, plans and privacy notice

- **Type:** feature
- **Priority:** P0
- **Estimate:** 60 min
- **Rubric / Spec:** C1 · `IDEA.md` §0, §1, §10
- **Depends on:** HACK-003, HACK-016
- **Paths:** web/src/features/landing/, web/public/landing/
- **Freeze-Allowed:** yes
- **Acceptance:**
  - Built with the `landing-story` skill: the one line, the wow as a real screenshot of the live board, three steps and a "Probar la demo" button.
  - The Gratis / Pro / Equipos plans are labeled as a hypothesis. A short privacy notice and the AI-voice disclosure are included. It has no figure without a source in `IDEA.md` §10.
  - Screenshots at 1280×720 and 390×844.
- **Verify:** `npm --prefix web run build && bash .uak/bin/design-lint`
- **Next step:** take the live-board screenshot from the deployed app.

## HACK-024 · Demo and submission: README, script, plan-B video, clean-clone rehearsal

- **Type:** demo
- **Priority:** P0
- **Estimate:** 60 min
- **Rubric / Spec:** C1 · `.uak/modes/sprint.md` §Submission checklist
- **Depends on:** HACK-013, HACK-016, HACK-019
- **Paths:** README.md, docs/demo/
- **Freeze-Allowed:** yes
- **Acceptance:**
  - `README.md` in English: what it is, real screenshots, setup (`uv sync`, `npm ci`), the `.env.example` variables, how to run with `DEMO_MODE=1` and no keys, the deploy URL, and licenses.
  - `docs/demo/script.md` is a timed 3-minute script with the wow at 90 s or earlier, and a fallback per step.
  - The plan-B video link is recorded in `docs/demo/`, and a rehearsal from a clean clone is logged.
- **Verify:** `test -s README.md && test -s docs/demo/script.md && bash .uak/bin/smoke`
- **Next step:** write `docs/demo/script.md` from `IDEA.md` §4.

## HACK-059 · The board view no longer throws "undefined is not valid JSON" when its event stream closes

- **Type:** bug
- **Priority:** P0
- **Estimate:** 30 min
- **Rubric / Spec:** `IDEA.md` §4 step 3 (the board)
- **Depends on:** None
- **Paths:** web/src/features/live-board/useBoardEvents.ts, e2e/judge_path.py
- **Acceptance:**
  - Found on https://speedhack.onrender.com (2026-10-30, run `run_f5460ad2`): opening `/?run=ID#/live-board` logs two page errors `"undefined" is not valid JSON`. `useBoardEvents.ts:24` parses every event with `JSON.parse(m.data)`, and the browser's own `error` event (stream closed or reconnecting) has no data. The run view had the same bug and fixed it in HACK-034.
  - Events without data, or with data that is not JSON, are ignored (the stream's own reconnect keeps working); a named `error` event that carries a StageEvent still reaches the view.
  - `e2e/judge_path.py` fails if the board view logs any page error while the run is finished (the stream closes), and passes after the fix; checked once against the unfixed hook.
- **Verify:** `npm --prefix web run build && bash .uak/bin/design-lint && uv run python e2e/judge_path.py`
- **Next step:** read `useBoardEvents.ts` and how `web/src/features/run/` guards the same parse.

## HACK-060 · The board's standalone example plays the real recording, not its own sample data

- **Type:** chore
- **Priority:** P1
- **Estimate:** 40 min
- **Rubric / Spec:** `IDEA.md` §3
- **Depends on:** None
- **Paths:** web/src/features/live-board/demo.ts, scripts/demo_from_recordings.py, app/tests/test_demo_fixture.py
- **Acceptance:**
  - `#/live-board` without `?run=` today plays its own invented example (Login, Empresa, GAS-1…GAS-8), which tells a different story from the recorded plan the rest of the demo shows (HACK-053/054).
  - `scripts/demo_from_recordings.py` also fills a `// <recorded>` block in `web/src/features/live-board/demo.ts` with the same board (what `miro.BoardRun` emits for `architecture.json`, colors dropped) and the 6 recorded issues; the replay keeps its timing and labels everything `demo_data: true`.
  - Running the script twice leaves no diff; the replay at 1280×720 shows no overlapping labels and no page scroll.
- **Verify:** `uv run pytest -q && uv run ruff check app scripts && npm --prefix web run build && bash .uak/bin/design-lint && uv run python e2e/judge_path.py`
- **Next step:** read `web/src/features/live-board/demo.ts` and the `WEB` table of `scripts/demo_from_recordings.py`.

## HACK-061 · Pitch Q&A does not answer an unrelated question with a quote that only shares one word

- **Type:** bug
- **Priority:** P1
- **Estimate:** 40 min
- **Rubric / Spec:** `IDEA.md` §4 step 7 · PROJECT principle 4
- **Depends on:** None
- **Paths:** app/services/pitch.py, app/tests/test_pitch_unrelated.py
- **Acceptance:**
  - `ask()` keeps any passage that shares one word with the question, so "¿Cuál es el precio del dólar hoy?" can quote a competitor's research note because both contain "precio" (seen while reviewing HACK-058).
  - A question about something the project does not cover answers "no tengo ese dato"; questions about the project's competitors, prices, features, alerts and its general purpose keep their current answers and sources (HACK-058 tests unchanged).
  - New tests cover the dollar question, a competitor-price question and an alerts question, in DEMO_MODE and with the LLM stubbed; no existing test is edited.
- **Verify:** `uv run pytest -q && uv run ruff check app && uv run python e2e/judge_path.py`
- **Next step:** read `ask()` and `_words()`; measure which passages each question keeps today before changing the rule.

## HACK-062 · Docs describe the product, not the hackathon

- **Type:** docs
- **Priority:** P1
- **Estimate:** 30 min
- **Rubric / Spec:** `.uak/PROJECT.md` §Purpose
- **Depends on:** None
- **Paths:** README.md, IDEA.md, docs/demo/
- **Acceptance:**
  - README no longer addresses judges ("Judges should wait…", "the board wow starts at 00:55") and states plainly what the public deployment is: demo mode, recorded data, no accounts, free plan that sleeps after 15 minutes.
  - `IDEA.md` keeps its content but its header says the hackathon was phase 0 and SpeedHack is now Dylan's own product; event-only items (rubric C1, plan-B video deadline) are marked historical, not deleted.
  - No figure, URL or date is invented; the links in the README still resolve.
- **Verify:** `bash .uak/bin/q bash -c 'test -s README.md && bash .uak/bin/smoke'`
- **Next step:** list every hackathon reference with `rg -n -i "juez|judge|hackathon|jury|rubric|C1|plan-b|submission" README.md IDEA.md docs/`.

## HACK-063 · Research finds real competitors of the idea, not job guides and stock quotes

- **Type:** bug
- **Priority:** P0
- **Estimate:** 1 day
- **Rubric / Spec:** `.uak/PROJECT.md` principle 4 · `IDEA.md` §4 step 2
- **Depends on:** None
- **Paths:** app/services/research.py, app/services/stages.py, app/services/llm.py, app/services/prompts/research_query.md, app/tests/test_research_query.py
- **Acceptance:**
  - Found in the real run `run_242dc4bf` (2026-10-30, client mode, "catálogo de bombas de agua y motores"): the 5 results were an Indeed guide to starting a clothing business, Indeed articles on marketing and SMEs, a Kraken stock quote and a CB Insights page read as pricing "$1". Cause: `_research_stage` sends the idea plus the answers, cut at 200 characters, with " competitors pricing Mexico" appended (`research.py:192`).
  - The query is built from the idea's product, customer and market (the LLM writes 1–3 short search queries from the idea; it never writes a result, a figure or a URL), in the idea's language, with the country only when the idea names one.
  - Results whose page is not about a product, company or service in that market (job guides, news, stock quotes, generic how-tos) are dropped before they reach the plan; an empty result says so in the conversation instead of padding it.
  - `pricing` is kept only when the price sits next to a product or plan name on that page; a lone "$1" is not a price.
  - Tests with recorded Tavily responses (no network) cover the pump-catalog idea and the expense-SaaS idea; one real run with keys is reported in the PR (top 5 titles and URLs).
- **Verify:** `uv run pytest -q && uv run ruff check app`
- **Next step:** write the failing test with the recorded junk results of `run_242dc4bf`, then the query builder.

## HACK-064 · A failed stage in a real run says so; it never shows another project's recording

- **Type:** bug
- **Priority:** P0
- **Estimate:** 1 day
- **Rubric / Spec:** `.uak/PROJECT.md` principle 4
- **Depends on:** None
- **Paths:** app/services/pipeline.py, app/services/miro.py, app/services/stages.py, app/tests/test_live_failures.py, web/src/features/project/
- **Acceptance:**
  - Found in `run_242dc4bf`: Miro answered `500 Internal error occurred` on a sticky note after its retries, stage 5 raised, and `pipeline._produce` replayed `app/fixtures/demo/run.jsonl` stage 5 — the expense-SaaS board ("Dashboard de gastos"…) in a pump-catalog project. Half a real board was left in Miro.
  - Outside `DEMO_MODE`, a stage that raises emits an `error` event with a Spanish message naming the provider and what to do, keeps the run waiting on that stage, and offers "Reintentar"; it never replays the recorded run. `DEMO_MODE` keeps today's replay.
  - Miro: a note that still fails after its retries is skipped and reported; the notes and frames already created are kept, and the stage finishes with what exists (`demo_data: false`).
  - `#/project` shows the error card with "Reintentar"; retrying reuses the ids already created (no duplicate board or issues).
  - Tests: a stub provider that raises in a live run produces the error event and no fixture events; a Miro stub that fails one note keeps the others.
- **Verify:** `uv run pytest -q && uv run ruff check app && npm --prefix web run build && bash .uak/bin/design-lint && uv run python e2e/judge_path.py`
- **Next step:** failing test for the replay in `_produce` (live mode), then the error event.

## HACK-065 · The whole pitch is narrated with Dylan's ElevenLabs voice

- **Type:** feature
- **Priority:** P0
- **Estimate:** 1 day
- **Rubric / Spec:** `IDEA.md` §4 step 7
- **Depends on:** None
- **Paths:** app/services/pitch.py, app/services/voice.py, app/routers/pitch.py, app/services/prompts/narration.md, app/fixtures/voice/, app/tests/test_pitch_narration.py, web/src/features/pitch/
- **Acceptance:**
  - Today only the Q&A answers are spoken (`/api/voice/tts`); the slides are silent text cards.
  - Every slide gets a short spoken script (2–4 sentences, Spanish) written only from that slide's title, bullets and sources; the script is validated (no figure or name absent from the slide) before it is used.
  - The pitch room has "Presentar con voz": it plays each slide's script with the voice in `ELEVENLABS_VOICE_ID` (never another voice), advances to the next slide when it ends, and has pause, resume and stop; the Q&A answers keep using the same voice. The narration starts with the AI disclosure once.
  - Audio is generated once per slide and cached per run; without a key or in `DEMO_MODE` a recorded narration of the demo deck plays, labeled demo.
  - Keyboard operable; visible "Narrado por IA" while it plays; if the voice fails, the slide text stays and a Spanish message says the voice is unavailable.
- **Verify:** `uv run pytest -q && uv run ruff check app && npm --prefix web run build && bash .uak/bin/design-lint && uv run python e2e/judge_path.py`
- **Next step:** failing test for the per-slide script validation, then the narration endpoint.

## HACK-066 · The pitch is a real presentation, not text cards

- **Type:** feature
- **Priority:** P0
- **Estimate:** 1 day
- **Rubric / Spec:** `IDEA.md` §4 step 7 · `web/DESIGN.md`
- **Depends on:** None
- **Paths:** web/src/features/pitch/, app/services/pitch.py, app/tests/test_pitch_deck.py
- **Acceptance:**
  - Today the deck is cards with a title, bullets and a "SpeedHack · Pitch" label; in `DEMO_MODE` it has 2 slides built from memory, and the recorded 6-slide deck (`app/fixtures/llm/deck.json`) is never shown.
  - Slides are 16:9, designed with the project's tokens: a cover with the project's name and one line, one idea per slide with a large title, at most 4 bullets, and sources as small footnotes; a full-screen presenter mode (arrows, Esc) and "Exportar PDF" with one slide per page.
  - A real run shows the deck the LLM built; `DEMO_MODE` shows the recorded deck of the demo case; no slide shows a source that is not in that run's research.
  - Verified in a real browser at 1280×720 and 390×844: no overlap or clipped text; PDF export of a 5-slide deck has 5 pages.
- **Verify:** `uv run pytest -q && npm --prefix web run build && bash .uak/bin/design-lint && uv run python e2e/judge_path.py`
- **Next step:** failing test that the demo deck uses `deck.json`, then the slide layout.

## HACK-067 · Pitch Q&A is labeled real in a real run and does not ground answers on irrelevant pages

- **Type:** bug
- **Priority:** P1
- **Estimate:** 0.5 day
- **Rubric / Spec:** `.uak/PROJECT.md` principle 4
- **Depends on:** HACK-063
- **Paths:** app/services/pitch.py, app/services/memory.py, app/tests/test_pitch_live.py
- **Acceptance:**
  - In `run_242dc4bf` every answer came back `demo_data: true` (local memory recall marks every passage demo), "¿Quiénes son los competidores?" said "no tengo ese dato", and "¿Cómo pide una cotización el cliente?" answered about WhatsApp citing the CB Insights page.
  - Passages recalled for a real run keep `demo_data: false`; only recorded or demo passages are demo.
  - A competitor question answers from the run's research notes with their URLs; an answer is rejected when its cited passage does not contain the facts it states.
- **Verify:** `uv run pytest -q && uv run ruff check app`
- **Next step:** failing test on the demo flag of a live run's recall.

## HACK-068 · Spike: SpeedHack creates the product in Lovable through the Lovable MCP server

- **Type:** spike
- **Priority:** P0
- **Estimate:** 1 day
- **Rubric / Spec:** `IDEA.md` §4 step 4 · feeds spec 002 (real product)
- **Depends on:** None
- **Paths:** scripts/spikes/lovable_mcp.py, docs/specs/002-real-product/spike-lovable.md
- **Acceptance:**
  - Lovable documents AI project creation through its MCP server at `https://mcp.lovable.dev` (`create_project`, deploy and cloud-database tools; OAuth with the user's Lovable account; every plan, consumes credits; research preview): https://docs.lovable.dev/integrations/lovable-mcp-server.md. SpeedHack today only builds a "Build with URL" link (`generator.LovableGenerator`).
  - A server-side script authenticates once with Dylan's Lovable account (OAuth, done by Dylan in the browser; no token in the repo, logs or chat), sends the build prompt `generator.build_prompt` makes for `run_242dc4bf`, and records: the tools the server lists, whether `create_project` returns a project id and a preview or published URL, the time to a working app, the credits used, and the errors.
  - `spike-lovable.md` reports those facts with the commands run and a go/no-go for using it in stage 7, including how a server keeps a user's OAuth token safe; nothing is integrated into the app in this task.
- **Verify:** `test -s docs/specs/002-real-product/spike-lovable.md && uv run ruff check scripts`
- **Next step:** read the MCP server docs; Dylan authorizes the OAuth login and the credit spend before the first call.

## HACK-069 · All four quality checks run on Render, or the decision not to is recorded

- **Type:** chore
- **Priority:** P1
- **Estimate:** 0.5 day
- **Rubric / Spec:** `.uak/PROJECT.md` §Environments
- **Depends on:** None
- **Paths:** Dockerfile, render.yaml, docs/adr/0001-render-quality-checks.md
- **Acceptance:**
  - On https://speedhack.onrender.com only "lint" and "secrets" run: the runtime image (`python:3.12-slim`) has no Node and no browser, so "build" and "smoke" are reported as not run (seen 2026-10-30, `run_f5460ad2`).
  - Measure the image size and peak memory of a run with Node + Playwright Chromium added; if it fits the Render plan in use, add them and verify the four checks on Render; if not, write the ADR with the numbers and the alternative (a larger plan, or running build/smoke elsewhere).
- **Verify:** `test -s docs/adr/0001-render-quality-checks.md || docker build -t speedhack-check .`
- **Next step:** build the image locally with Node + Chromium and measure.

## HACK-070 · Research debt from the HACK-063 security review

- **Type:** follow-up
- **Priority:** P1
- **Estimate:** 0.5 day
- **Rubric / Spec:** `.uak/PROJECT.md` principles 1 and 4
- **Depends on:** HACK-063
- **Follow-up of:** HACK-063
- **Paths:** app/routers/runs.py, app/services/stages.py, app/tests/test_research_debt.py, web/src/features/project/
- **Acceptance:**
  - Security review of HACK-063 (dylan-3, SHA d882c0c, 2026-10-30) found two LOW issues and two criteria declared as debt.
  - `POST /api/projects` caps `idea` (and each answer) with a `max_length`, answering 422 in Spanish above it; the LLM never receives more than that.
  - The research stage never logs the idea, the answers or the LLM's invalid queries: an `LLMOutputError` is logged by type only.
  - When research finds no competitor, the conversation (`#/project`) shows that notice to the user, not only the spec stage.
  - One real run with keys (within the test budget) is reported in the PR: top 5 titles and URLs for the pump-catalog idea.
- **Verify:** `uv run pytest -q && uv run ruff check app && npm --prefix web run build && bash .uak/bin/design-lint`
- **Next step:** failing tests for the 422 cap and the log content.
