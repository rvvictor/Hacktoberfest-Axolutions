# Spec 001 · Accounts and spending limits
- Status: draft · Owner: Dylan · PROJECT principles: 1 (secure and private by default), 4 (no invented figures)

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
- As a user, I want to sign in, so that my projects are mine and nobody else can read, answer or approve them.
- As a user, I want to see how many runs I have left, so that a limit never surprises me in the middle of a project.
- As the owner, I want a cap per user and a global cap on paid calls, so that one person or a script cannot drain the provider credit.
- As the owner, I want outreach (Hunter) available only to me, so that no visitor can send messages in my name.

## Acceptance criteria (EARS)
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
- Every number below is a proposal for Dylan to set; none is measured or decided yet:
  - runs per user per day: `<to decide, e.g. 3>`;
  - global paid calls per day: `<to decide, from the provider budget>`;
  - requests per minute per route and caller: `<to decide>`.
- Sessions in `HttpOnly`, `Secure`, `SameSite=Lax` cookies; no session token in URLs, logs or the browser's storage.
- Personal data kept: an email and the projects; nothing else. Account deletion removes both.
- The added auth check costs `<to decide>` ms at p95 per request.

## Out of scope
- Payments, plans and paid tiers.
- Teams and shared projects (one owner per project).
- Moving off SQLite (a separate spec once there is a production environment).
- Per-user provider keys ("bring your own key").

## Open questions
- [ ] How do people sign in: email magic link, Google/GitHub OAuth, or email + password? · answered by Dylan
- [ ] Who pays the provider calls of a user's run: the owner's keys (today) or the user's? · answered by Dylan
- [ ] The run, quota and budget numbers above · answered by Dylan
- [ ] Does Client mode (the barbershop journey) need an account, or stays a public recorded example? · answered by Dylan
- [ ] Where will it be deployed (it decides the session store and how the limits are shared between processes)? · answered by Dylan
