# ADR 0003 · Lovable builds users' apps through its MCP server with the owner's connection
- Status: accepted (Dylan, 2026-10-31) · Date: 2026-10-31 · Decider: Dylan

## Context
Dylan wants users to get a finished app inside SpeedHack, with no external step and no Lovable account, paid with
the owner's Lovable credit (spec 002). Lovable has no public build API; its "Build with URL" link only opens a prompt
in the visitor's own browser session. The HACK-068 spike showed that Lovable's MCP server (research preview) builds,
publishes and gives a database to an app, and accepts a server-side OAuth client (dynamic registration, PKCE, refresh).

## Decision
SpeedHack talks to `https://mcp.lovable.dev` from the server with the official `mcp` Python SDK, authorized once by
the owner. The owner's token set is stored encrypted (Fernet, key in the environment). All calls go through one
adapter, `app/services/lovable.py`. Builds for anyone but the owner stay behind `LOVABLE_PUBLIC=false` until Lovable
confirms in writing that its terms allow this use.

## Alternatives
- Keep the "Build with URL" link: the user leaves SpeedHack and pays with their own Lovable account. Dylan rejected it.
- Each user connects their own Lovable: still an external account and step for the user. Out of scope.
- Only SpeedHack's own generator: one HTML page with sample data, no real database or published app.
- Write a small MCP client over `httpx`: fewer dependencies, but we would own the OAuth and transport code.

## Consequences
- Users receive a published `*.lovable.app` app with a database. Lovable keeps the `lovable.app` domain.
- Every build spends the owner's credit (about 2.2 per first build, one measurement): it needs spec 001's quotas and a monthly cap.
- The MCP server is a research preview, so a change in its tools breaks only the adapter, and the fallback is SpeedHack's own prototype.
- Legal risk: Lovable's terms (updated 2026-08-28) forbid offering the Services to third parties "on a service bureau or time-sharing basis" and "automated tools" without written permission. The launch gate is the mitigation.
- Reversible: `LOVABLE_ENABLED=false` returns stage 7 to SpeedHack's own generator. Published apps stay in the owner's workspace until unpublished.
