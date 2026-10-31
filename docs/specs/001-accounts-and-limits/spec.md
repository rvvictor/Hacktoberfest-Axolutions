# Spec 001 · Accounts and spending limits
- Status: draft, answers from Dylan 2026-10-31 · Owner: Dylan · PROJECT principles: 1 (secure and private by default), 4 (no invented figures)
- Needed by: spec 002 (Lovable builds the product with the owner's credits), which spends paid credit per user.

## Problem
Today no API route asks who is calling (checked on `main` 740fd0e: no route in `app/routers/` uses an auth dependency and
`app/main.py` adds no auth middleware). Anyone who can reach the server can:
- start a run (`POST /api/projects`), and with keys configured that run spends Tavily, Firecrawl, Gemini, Miro and
  Linear credit and writes real issues and boards in the owner's accounts;
- answer and approve any run, read any run and its events, and open any generated prototype, knowing only its id;
- call the LLM through the pitch room (`POST /api/pitch/{run_id}/ask`) and the voice routes (`/api/voice/stt`, `/tts`),
  and get a signed voice-session URL (`GET /api/voice/session`);
- draft, approve and send outreach messages (`/api/hunter/...`).
Nothing limits how many runs or calls one caller makes. SpeedHack cannot be published like this.

## Stories
- As a visitor, I want to try the recorded example without an account, so that I see what SpeedHack does before signing up.
- As a user, I want to sign in with my Google account, so that my projects are mine and nobody else can read, answer or approve them.
- As a user, I want to see how many runs I have left, so that a limit never surprises me in the middle of a project.
- As the owner, I want a cap per user and a global cap on paid calls, so that one person or a script cannot drain the provider credit.
- As the owner, I want outreach (Hunter) available only to me, so that no visitor can send messages in my name.

## Acceptance criteria (EARS)
- When a visitor chooses "Entrar con Google", the system shall sign them in with Google (OpenID Connect, authorization code with PKCE and `state`), keep only their verified email and Google subject id, and create the account on the first sign-in.
- If Google answers with an error, a mismatched `state` or an unverified email, the system shall not create a session and shall say in Spanish that the sign-in failed and how to retry.
- When a request without a valid session reaches a route that creates, reads, answers, approves or asks about a run, the system shall answer 401 and do no provider call.
- When a signed-in user requests a run, prototype, event stream or pitch of another user, the system shall answer 404 (not 403, so ids are not confirmed).
- When a signed-in user creates a project, the system shall record the user as its owner, and every later read and write of that run shall check that owner.
- While `DEMO_MODE` is on, the recorded example (`#/project` without `?run=`, `demo-pitch`) shall stay usable without an account and shall make no provider call.
- When a user reaches their run quota for the period, the system shall refuse the new project with 429, say in Spanish how many runs they used and when the quota resets, and start no stage.
- When the global daily budget of paid calls is reached, the system shall refuse new projects for everyone with 503 and a Spanish message, and shall let runs already in progress finish their current stage.
- When a caller sends more requests to one route than the per-minute limit, the system shall answer 429 with `Retry-After`.
- If a non-owner calls any `/api/hunter/` route, the system shall answer 403 and send nothing.
- When a run is refused or limited, the system shall log the user id, the route and the reason, and shall not log the idea text, answers or keys.

## Non-functional
- Numbers (Dylan, 2026-10-31, unless marked proposal):
  - new projects per user per day: **1** (decided; the owner pays every provider call, including the Lovable build of spec 002);
  - global new projects per day: proposal **5**, a setting (`MAX_PROJECTS_PER_DAY`), so a burst of sign-ups cannot drain the credit; it is not derived from a measured budget;
  - requests per minute per route and user: proposal **30**, a setting.
- Who pays: the owner's keys pay every provider call (Dylan, 2026-10-31). Plans and prices that cover the cost come later (out of scope).
- Sessions in `HttpOnly`, `Secure`, `SameSite=Lax` cookies; no session token in URLs, logs or the browser's storage.
- Personal data kept: an email and the projects; nothing else. Account deletion removes both.
- The added auth check costs at most 20 ms at p95 per request (proposal; measured in the PR that adds it).
- Deployment: Render (Dylan, 2026-10-31). The free plan's disk is not persistent and the service sleeps, so accounts and quotas need a persistent store there (a paid persistent disk for SQLite, or a managed database); the choice and its cost go in an ADR before any task that needs it.

## Out of scope
- Payments, plans and paid tiers.
- Teams and shared projects (one owner per project).
- Moving off SQLite beyond what the Render ADR decides.
- Sign-in methods other than Google (GitHub or email can be added later).
- Per-user provider keys ("bring your own key").

## Open questions
- [x] How do people sign in? · Google (Dylan, 2026-10-31)
- [x] Who pays the provider calls of a user's run? · the owner's keys (Dylan, 2026-10-31)
- [x] Runs per user · 1 new project per day (Dylan, 2026-10-31); the global and per-minute numbers above are proposals
- [x] Does Client mode need an account? · no: it stays a public recorded example with no provider call (default taken by the agent; Dylan can change it)
- [x] Where will it be deployed? · Render (Dylan, 2026-10-31)
- [ ] Creating the Google OAuth client (Google Cloud project, consent screen) needs Dylan's Google account · Dylan
- [ ] Global projects per day and requests per minute: keep the proposals (5 and 30)? · Dylan
