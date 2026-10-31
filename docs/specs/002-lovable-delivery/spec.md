# Spec 002 · Lovable builds the product and SpeedHack delivers it
- Status: approved (Dylan, 2026-10-31) · Owner: Dylan · PROJECT principles: 1 (secure and private by default), 3 (ADR for costly decisions), 4 (no invented figures)
- Depends on: spec 001 (accounts and limits). Decision record: ADR 0003.
- **Launch gate:** no public user gets a Lovable build until Lovable confirms in writing that this use fits its terms (see Open questions); until then it runs only for the owner. Facts from the HACK-068 spike: `docs/specs/002-real-product/spike-lovable.md`.

## Problem
Today stage 7 gives the user SpeedHack's own one-page prototype (sample data in the browser, no real login or
database) and a "Construirlo en Lovable" link. That link sends the user out of SpeedHack to lovable.dev, where the
build needs their own Lovable account and credit, and SpeedHack never learns what was built.

Dylan wants the user to receive the finished product **inside SpeedHack, with no external step and no Lovable
account**, paid with the owner's Lovable credit (Dylan, 2026-10-31). Plans that cover that cost come later.

What the HACK-068 spike measured (2026-10-30, one build, from this Claude Code session):
- Lovable's MCP server (`https://mcp.lovable.dev`, a research preview) exposes `create_project`, `send_message`,
  `get_project`, `deploy_project`, `enable_database`, among others.
- One `create_project` call with the plan built a working app in ≤ 137 s for `cost_credits: 2.2`.
- The preview URL answers 401 without a Lovable session; a published app lives on `*.lovable.app`.
- A server can act on the owner's behalf through OAuth (dynamic client registration, authorization code with PKCE,
  refresh token; scopes `projects:create`, `projects:write`, `workspaces:read`, `offline`).

## Stories
- As a user, after I approve my tasks, I want SpeedHack to build my app and show it to me working, so that I get a product without leaving SpeedHack or having a Lovable account.
- As a user, I want my app to keep real data (its own database), so that it is a product and not a mock-up.
- As a user, I want to ask for a change in my own words and see the app updated, so that I can shape it without another tool.
- As a user, I want a link I can share, so that others can use my app.
- As the owner, I want every build paid from my Lovable workspace with a cap, so that my credit is never drained, and I want to see the credit each run spent.
- As the owner, I want SpeedHack's own prototype to stay as the fallback, so that a user always gets something when Lovable fails or the cap is reached.

## Acceptance criteria (EARS)
- When the user approves stage 6 (tasks) and the owner's Lovable connection and credit cap allow it, the system shall create a Lovable project in the owner's workspace from the approved plan and backlog, and shall show the build's progress in the conversation (`#/project`) in plain Spanish.
- When the build completes, the system shall give the project a database, publish it, and show the published app inside SpeedHack with its public link, labeled as built with Lovable.
- When the user sends a change request (at most 1,000 characters) for their published app, the system shall send it to that project, show the progress, republish, and show the updated app; each project accepts at most a set number of change requests.
- If Lovable answers with an error, takes longer than the build timeout, pauses for a tool approval, or asks for a secret, the system shall stop that build, show SpeedHack's own prototype with a Spanish message saying the Lovable build did not finish, and shall never ask the user for a credential.
- If the owner's Lovable credit cap for the period is reached, or the owner's Lovable connection is missing or expired, the system shall build SpeedHack's own prototype instead and say so; it shall not start a Lovable call.
- While `DEMO_MODE` is on, the system shall make no Lovable call and shall show a recorded result labeled `demo_data: true`.
- When a build or change finishes, the system shall record the credit Lovable reports for it against the run, and `/api/ops` shall show it; no credit figure is estimated or invented.
- When a signed-in user asks for another user's Lovable project, build status or change history, the system shall answer 404.
- When a user's account is deleted, the system shall unpublish that user's Lovable apps (Dylan, 2026-10-31).
- While the launch gate is closed (`LOVABLE_PUBLIC=false`), only the owner's runs shall use Lovable; every other run gets SpeedHack's own prototype.
- The system shall keep the owner's Lovable tokens only on the server, encrypted at rest, and never in the browser, URLs, logs, events or the repository.
- When the user's idea or a change request is sent to Lovable, the system shall send it as data inside the build instructions, together with the content rules of the owner's terms; if Lovable refuses the content, the system shall stop and say so.

## Non-functional
- Build time: from approval to a published app, p95 ≤ 5 minutes (one spike build took ≤ 137 s; to be measured on real runs).
- Credit: Dylan's Lovable plan has 100 credits a month (Dylan, 2026-10-30); a build costs about 2.2 (one measurement). A monthly cap setting (`LOVABLE_MONTHLY_CREDITS`, 100) stops new builds at 80 % of it, and each project accepts at most 3 change requests (Dylan, 2026-10-31).
- Privacy: SpeedHack stores per run only the Lovable project id, its published URL and the credit spent; the user's app data lives in that app's database, not in SpeedHack.
- The Lovable connection is a research preview: every call goes through one adapter, so a change in its tools touches one file.

## Out of scope
- Plans, prices and payments that cover the cost (Dylan: later).
- Users connecting their own Lovable account.
- Exporting the code to GitHub or handing the Lovable project over to the user.
- Custom domains for the published app.

## Open questions
- [ ] **Do Lovable's terms allow this?** Read 2026-10-31 (https://lovable.dev/terms, updated 2026-08-28): the license is "for your personal or internal business purposes" and lets "your end users … access and use those projects", but it forbids making the Services "available to any third party on a service bureau or time-sharing basis" and using "automated tools … to access or interact with the Services" without written permission. Building apps for SpeedHack's users from one workspace through MCP is close to both. **Ask support@lovable.dev for written permission before the launch gate opens** · Dylan
- [x] Can a published `*.lovable.app` be shown inside SpeedHack? · yes: measured 2026-10-31, https://pump-motor-quote-catalog.lovable.app sends no `X-Frame-Options` or `frame-ancestors` and renders inside an iframe in Chromium; if that changes, the app opens in a new tab (Dylan's fallback)
- [x] Credit cap 80 % of 100 credits a month and 3 change requests per project · yes (Dylan, 2026-10-31)
- [x] Who may see a published app? · anyone with the link, Lovable's default (taken by the agent: Dylan did not know; the user wants to share it)
- [x] What happens to a user's app when they delete their account? · it is unpublished (Dylan, 2026-10-31)
