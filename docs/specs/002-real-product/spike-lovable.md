# Spike HACK-068 · Creating the product in Lovable through its MCP server

- Date: 2026-10-30 · Author: dylan-3 · Budget: Lovable cap 50 credits (Dylan, 2026-10-30); spent **2.2**.
- Client: this Claude Code session, with Dylan's Lovable account already authorized (OAuth in the browser).
  Decision recorded: the spike measures the server first; a server-side client is assessed from the OAuth metadata.

## What was sent
`generator.build_prompt` for the real run `run_242dc4bf` (client mode, pump and motor catalogue): 2,013 characters
with the problem, users, MVP features, assumptions and the 5-item backlog. Reproduce with
`uv run python scripts/spikes/lovable_mcp.py run_242dc4bf`.

## Results
| Question | Answer (measured) |
|---|---|
| Tools exposed | `create_project`, `send_message`, `get_message`, `get_project`, `get_diff`, `list_files`, `read_file`, `deploy_project`, `enable_database`, `get_database_status`, `query_database`, `add_connector`, `list_connectors`, `set_project_knowledge`, `remix_project`, analytics, workspace skills, among others |
| Does `create_project` build the app? | Yes. One call (`wait: true`) created project `3b7c2d67-adb0-45e1-befd-90ce66ad8776` ("Bombas y Motores Pro") and returned `agent_response.status: completed`, `commit_sha`, `editor_url` and `preview_url` |
| Time to a working app | ≤ 137 s from the call to the result (upper bound: it includes this session's own turn) |
| Credits | `cost_credits: 2.2` for the whole first build |
| What it built | TanStack Router + Tailwind app: catalogue of 6 sample pumps and motors with features, MXN prices, "En existencia / Sobre pedido" badges and a type filter; "Cotizar" form (name, phone, email, message) validated with zod; business panel listing quotes, toggling stock and editing roles for 3 sample users in 2 sample businesses |
| What it simulated (its own report) | Data in the browser's `localStorage` (not shared); no real login (a "Sesión (demo)" selector); no email sent although the confirmation says it was; brand, products and prices invented as placeholders |
| Preview URL | `https://id-preview--…lovable.app` answers `401` without a Lovable session: it is private to the workspace |
| Published URL | Not tried: `deploy_project` publishes on `*.lovable.app` and was left for Dylan's explicit OK |
| Real backend | Available: `enable_database` provisions a PostgreSQL database (Supabase) per project, and Lovable offers auth, storage and edge functions; not enabled in this spike |
| Errors | None |

## Can SpeedHack do this from its server?
Yes, per the published OAuth metadata (`uv run python scripts/spikes/lovable_mcp.py --discovery`):
- protected resource `https://mcp.lovable.dev`, authorization server `https://lovable.dev/oauth`;
- dynamic client registration (`/oauth/register`), authorization code with PKCE (`S256`), `refresh_token`;
- scopes `projects:create`, `projects:write`, `workspaces:read`, `offline`.

A server can register itself once, send each user through Lovable's consent screen once, and keep a refresh token
to act later. That needs SpeedHack accounts (spec 001) and the token stored encrypted per user, never in logs,
URLs or the browser. The MCP server is a **research preview**: its tools or limits can change.

## Go / no-go for stage 7
**Go, behind accounts.** With a Lovable connection, stage 7 calls `create_project` with the plan, then
`enable_database` so quotes and users are real, shows the preview inside SpeedHack (it needs the user's Lovable
session, or a publish), and keeps the in-house generator as the fallback when the user has no Lovable connection or
the call fails. Cost seen: 2.2 credits per first build; follow-up `send_message` iterations cost more credits each.

Next: spec 002 (real product) with these facts; Dylan decides whether to publish this spike app to see the
published URL flow (`deploy_project`).
