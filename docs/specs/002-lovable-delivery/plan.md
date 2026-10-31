# Plan 002 · Lovable builds the product and SpeedHack delivers it

## Design
- **Adapter:** `app/services/lovable.py` is the only module that talks to Lovable, through its MCP server (ADR 0003) with the official `mcp` Python SDK (streamable HTTP plus its OAuth client: dynamic client registration, PKCE, refresh). It exposes:
  - `build(prompt) -> Build(project_id, preview_url, credits)`: `create_project`, waits for completion, never more than `LOVABLE_BUILD_TIMEOUT`, default 600 s;
  - `add_database(project_id)`: `enable_database`;
  - `publish(project_id) -> url`: `deploy_project`, URL on `*.lovable.app`;
  - `change(project_id, text) -> credits`: `send_message`, then `publish`;
  - `unpublish(project_id)`: which MCP tool does this is checked in HACK-085. If none exists, `set_project_visibility` private, or an open question for Dylan.
  - A result with status `awaiting_input` (a tool approval or a secret form) raises `LovableNeedsInput`. SpeedHack never answers it, so the build stops and falls back.
  - With `DEMO_MODE` or no owner connection, every call raises `LovableUnavailable`. A recorded result in `app/fixtures/lovable/` serves the demo.
- **Owner connection:** `GET /api/admin/lovable/connect` and its callback (owner only, plan 001) run the SDK's OAuth flow once. The token set is stored encrypted with Fernet (`cryptography`, new dependency), keyed by `LOVABLE_TOKEN_KEY` in the environment, in table `secrets`, and refreshed tokens are written back. `GET /api/admin/lovable` says "conectado / no conectado" and the credit used this month.
- **Stage 7 (`stages._prototype_stage`):**
  - When `lovable.allowed(run)` holds (connected, under 80 % of `LOVABLE_MONTHLY_CREDITS`, and either `LOVABLE_PUBLIC` or the run's owner is the owner):
    1. `build(generator.build_prompt(spec, backlog))`;
    2. `add_database`;
    3. `publish`;
    4. emit `prototype_ready` with `generator: "lovable"`, `url` = published URL, `build_url` = None, `demo_data: false`.
  - Progress events tell the conversation where it is: "Construyendo tu app", "Conectando su base de datos", "Publicando".
  - On any `Lovable*` error or timeout it falls back to `SpeedHackGenerator` (today's path) with a recovered `error` event saying the Lovable build did not finish.
  - Alternative: keep building with SpeedHack and offer Lovable as an extra button. That is today's link with an extra step for the user, which Dylan ruled out.
- **Stage 8:** for a Lovable app, quality reads the project files through MCP (`list_files`, `read_file`) and runs the existing `lint` and `secrets` checks. `build` and `smoke` are reported as not run, never passed (HACK-087).
- **Changes:** `POST /api/runs/{id}/prototype/changes {text ≤ 1000}`, owner of the run only. At most 3 per project; the 4th returns 409 with a Spanish message. It runs `change` in the background and emits a new `prototype_ready`.
- **Delivery UI** (`#/project` card and `#/delivery`): the published URL in an `<iframe>` with `sandbox="allow-scripts allow-same-origin allow-forms allow-popups"`. That is safe because the app is on another origin, `*.lovable.app`, never SpeedHack's. The view also gets the "Abrir en otra pestaña" link, the "Pedir un cambio" box and "Hecha con Lovable". Framing was measured as allowed on 2026-10-31; if the frame fails to load, the link is the fallback.

## Data and migrations
- Expand:
  - `secrets(name PRIMARY KEY, ciphertext, updated)` for the owner's token set;
  - `costs` gains `credits REAL NULL` via `ADD COLUMN` (Lovable reports credits, not USD);
  - `external_ids(run_id, 7, 'lovable_project', id)` reuses the existing table, as do `lovable_url` and `lovable_changes`.
- No contract step. Rollback: `LOVABLE_ENABLED=false` sends stage 7 back to SpeedHack's own generator.

## Contracts
- The `prototype_ready` payload already has `generator`, `url`, `build_url` and `demo_data`. `generator: "lovable"` with a published `url` is new in meaning only; `Prototype.generator` already accepts `lovable`. `web/src/lib/types.ts` is unchanged.
- New event payloads for progress: a `stage_started` payload with `step: "build"|"database"|"publish"`. The front end shows them; older views ignore the field.
- New routes:
  - `POST /api/runs/{id}/prototype/changes`;
  - `GET /api/admin/lovable`, `GET /api/admin/lovable/connect`, `GET /api/admin/lovable/callback` (owner).
- `/api/ops` `costs` items gain `credits`.

## Threat model (STRIDE)
| Threat | Vector | Mitigation | Test |
|---|---|---|---|
| Spoofing | someone completes the owner's Lovable OAuth with their own account, or replays the callback | connect routes are `owner_only`; `state` + PKCE; callback accepts one pending `state` | non-owner → 403; wrong `state` → nothing stored |
| Tampering | prompt injection in the idea or a change request makes Lovable build something harmful in the owner's workspace | text goes as data inside the build prompt with the content rules; change text ≤ 1000 chars; Lovable's own refusals stop the build; 3 changes max | an idea with "ignora las instrucciones…" stays inside its data block in the prompt sent |
| Repudiation | which run spent which credit | credits per run in `costs`; `external_ids` links run ↔ project | ops shows credits per run |
| Information disclosure | owner token in logs, events, the browser or the repo; another user's app URL | Fernet at rest, key only in env; adapter never logs payloads; `run_for` gives 404 to other users | `caplog` and events contain no token; user B → 404 |
| Denial of service | users exhaust the owner's 100 monthly credits | 1 project/user/day (plan 001), 80 % monthly cap, 3 changes per project, `LOVABLE_PUBLIC` gate | at 80 % stage 7 uses SpeedHack and makes no Lovable call |
| Elevation of privilege | Lovable `awaiting_input` asks to approve a tool or a secret on the owner's account | never answered; build stops and falls back | an `awaiting_input` result → fallback, no `respond_to_approval` call |

## Observability
- Log per build: run id, Lovable project id, step, duration, credits, and outcome (`published`, `fallback:<reason>`). Never the prompt, the user's idea, URLs with tokens, or the token.
- `/api/ops`: credits this month against the cap. Proposed alert: log a warning at 60 % and 80 %.

## Rollout and rollback
1. HACK-082 to HACK-086 land with `LOVABLE_ENABLED=false`.
2. The owner connects Lovable locally and turns it on for the owner's own runs only (`LOVABLE_PUBLIC=false`).
3. Measure build time and credits on 3 real runs.
4. `LOVABLE_PUBLIC=true` only after Lovable's written OK on its terms and plan 001's `AUTH_REQUIRED=true`.
5. Rollback: `LOVABLE_ENABLED=false`.

## Cost
- Lovable: ~2.2 credits per first build (one measurement). Change requests cost more each, not measured. With 100 credits a month and the 80 % cap, that is about 36 first builds a month, fewer with changes.
- Per 1k users this is not reachable on Dylan's current plan. It is the input for the later pricing spec, not a commitment.
- `mcp` and `cryptography` are open-source dependencies with no runtime fee.

## Tasks
HACK-082 (adapter + fixtures), HACK-083 (owner connection + encrypted token), HACK-084 (stage 7 builds with Lovable + fallback + credits), HACK-085 (changes + unpublish on account deletion), HACK-086 (delivery UI: framed app, changes box), HACK-087 (quality on the Lovable app's files). Each starts with a failing test.
