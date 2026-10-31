# ADR 0002 · Accounts on Render need storage that survives a restart
- Status: proposed · Date: 2026-10-31 · Decider: Dylan

## Context
Spec 001 adds users, sessions, project owners and daily quotas. Today everything lives in SQLite under `DATA_DIR` on
the Render web service (`render.yaml`: `plan: free`). Render's free web services have no persistent disk and sleep
after 15 minutes idle, so a redeploy or restart would erase every account, session and quota count.
Dylan chose Render for the public version (2026-10-31).

## Decision (proposed)
Keep SQLite and give the service a Render persistent disk mounted at `DATA_DIR`, which needs a paid instance type.
It is the smallest change: no new driver, no migration of the store, and the current tests keep running.

## Alternatives
- Render PostgreSQL: survives restarts and allows more than one instance, but `app/services/store.py` is written for
  SQLite, so it means a store rewrite and a second service to pay for.
- An external managed database (for example Supabase or Neon): the same rewrite, plus another provider and its keys.
- Stay on the free plan: accounts would vanish on each deploy. Rejected.

## Consequences
- One instance only (a disk attaches to one instance); the per-minute rate limit can stay in process.
- Monthly cost = the paid instance plus the disk, priced from Render's pricing page when Dylan decides (no figure here).
- Reversible: copying the SQLite file out of the disk moves the data to another store later.
