# Plan 001 · Accounts and spending limits

## Design
- **Sign-in:** Google OpenID Connect, authorization code with PKCE and `state`, done with `httpx` (already a dependency).
  - `app/routers/auth.py` adds `GET /api/auth/google/login`, `GET /api/auth/google/callback`, `POST /api/auth/logout` and `GET /api/auth/me`. `main.py` auto-includes it.
  - The `id_token` comes straight from Google's token endpoint over TLS, so OIDC §3.1.3.7 lets us skip a signature library. We still check `iss`, `aud`, `exp` and `email_verified`.
  - Alternative: `authlib`. It is one more dependency for one provider, so we use it only if a second provider arrives.
- **Sessions:** an opaque random token in a cookie (`HttpOnly`, `Secure`, `SameSite=Lax`, `Path=/`). The server keeps only its SHA-256 in `sessions`, so a leaked database row cannot be replayed. Expiry: 30 days, and logout deletes the row.
  - Alternative: signed stateless cookies. Logout and account deletion could not revoke them.
- **Authorization:** one FastAPI dependency, `current_user` (401 without a session), plus `run_for(user, run_id)`, which answers 404 when the run is not the user's.
  - Every route in `runs.py`, `pitch.py`, `prototypes.py` and `voice.py` uses them.
  - `hunter.py`, `ops.py` and the Lovable owner routes (plan 002) use `owner_only`: the email must equal `OWNER_EMAIL`, otherwise 403.
- **Public demo:** the recorded example needs no account. `#/project` without `?run=` never calls the API. `demo-pitch` and `/fixtures/` stay anonymous while `DEMO_MODE` is on.
- **Limits:** run quotas are counted from `projects.owner_id` and `created`: 1 per user per UTC day (429) and `MAX_PROJECTS_PER_DAY` = 5 for everyone (503).
  - Per-minute limits are an in-process token bucket per (user, route), 30 per minute (429 with `Retry-After`).
  - One Render instance, so in-process is enough; a second instance moves the bucket to the database (ADR 0002).
- **Rollout flag:** `AUTH_REQUIRED` (default false). While it is false, everything behaves as today, so local development and the current public demo keep working while tasks land.

## Data and migrations
- Expand:
  - new tables `users(id, google_sub UNIQUE, email, created)` and `sessions(token_sha256 PRIMARY KEY, user_id, expires)`;
  - `projects.owner_id TEXT NULL` and `projects.created REAL NULL`, added with `ALTER TABLE … ADD COLUMN` when the column is missing (SQLite cannot add a column with `IF NOT EXISTS`).
- Migrate: existing projects keep `owner_id NULL`. They count as the owner's legacy runs and only the owner can read them.
- Contract: none. Rollback = `AUTH_REQUIRED=false`, and the columns stay unused.
- Account deletion: `DELETE /api/auth/me` removes the user, their sessions, projects, runs and events, and (plan 002) unpublishes their Lovable apps.

## Contracts
- `GET /api/auth/me` returns `{email, runs_left_today, resets_at}`, or 401.
- Every existing `/api/runs/*`, `/api/projects`, `/api/pitch/*`, `/api/prototypes/*` and `/api/voice/*` route gains 401 / 404 / 429 / 503. The Spanish message is in `detail`.
- Web: `web/src/lib/api.ts` maps 401 to the sign-in prompt and shows `detail` for 429/503. `web/src/lib/types.ts` gains `Me`.

## Threat model (STRIDE)
| Threat | Vector | Mitigation | Test |
|---|---|---|---|
| Spoofing | forged OAuth callback, login CSRF | `state` + PKCE bound to a short-lived cookie; `iss`/`aud`/`exp`/`email_verified` checked | callback with a wrong `state` or `aud` → no session |
| Tampering | editing another user's run by id | `run_for` checks `owner_id` on every read and write | user B gets 404 on A's run, events, pitch, prototype |
| Repudiation | who started a run that spent credit | log user id, route, reason on refusals; `owner_id` on every project | log line has user id and no idea text |
| Information disclosure | session token in logs or URLs; ids confirm existence | token only in cookie, hashed at rest; 404 instead of 403 | `caplog` has no token; 404 body equals unknown-run body |
| Denial of service | one user or script drains credit | 1/day per user, 5/day global, 30/min per route | 2nd project → 429; 6th global → 503; 31st request → 429 |
| Elevation of privilege | a user reaches Hunter or Ops | `owner_only` on `/api/hunter/*`, `/api/ops*` and Lovable owner routes | non-owner → 403, nothing sent |

## Observability
- Log lines with `user_id`, route and reason for 401/403/404-of-other/429/503, never idea text, answers, emails or tokens.
- `/api/ops` (owner) shows runs per user per day.

## Rollout and rollback
1. Land the tasks with `AUTH_REQUIRED=false`.
2. The owner signs in on a local run.
3. Turn on `AUTH_REQUIRED=true` on Render after ADR 0002 gives it persistent storage.
4. Rollback: flip the flag back.

## Cost
- No new paid service for auth: Google sign-in costs nothing.
- Render persistent storage costs what ADR 0002 picks, priced from Render's page when Dylan decides (not estimated here).
- Provider cost per user is capped at 1 run a day.

## Tasks
HACK-076 (sign-in), HACK-077 (ownership and 401/404), HACK-078 (quotas and rate limit), HACK-079 (web sign-in), HACK-080 (Render storage per ADR 0002), HACK-081 (account deletion). Each starts with a failing test.
