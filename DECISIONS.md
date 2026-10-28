# DECISIONS

Coordination decisions on the claims branch.
Why: a reversible option after 15 min keeps work moving.
- 1793157589 | deadline backlog/proposed/1793143081 | ALLOW_P0 | Only P0 with active autonomy; a timeout grants no permissions.
- 1793158535 | HACK-002 | payload validated per event type in test; ts = relative seconds | Why: contract for downstream tasks
- 1793158634 | HACK-001 | keep oxlint from Vite template | Why: template ships oxlint, not eslint
- 1793159248 | HACK-004 | fixtures hand-written, no ANTHROPIC key | Why: cannot make real call
- 1793159302 | HACK-013 | Hold PR/uak done until HACK-001/002 integrate (branch carries their merge) | Why: diff outside Paths otherwise
- 1793159442 | HACK-003 | Direction 3 Línea 1 | Why: human pick
- 1793159885 | HACK-006 | tests con asyncio.run, sin pytest-asyncio | Why: evitar tocar pyproject compartido
- 1793159895 | HACK-007 | fixtures hand-written, no LINEAR key | Why: cannot record real call
- 1793159895 | HACK-008 | httpx direct to ElevenLabs REST (respx-mocked), not SDK; fixtures are placeholders marked demo_data | Why: no API key yet; keeps tests offline
