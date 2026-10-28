# Lessons (uak learn)

Append-only. Format: - N | epoch | agent | task | paths | text. `uak recall` and `uak next` show the ones for your paths.

- 1 | 1793164317 | dylan-1 | HACK-016 | web/src/features/live-board/ | lib/sse.ts subscribe() uses onmessage but runs router (HACK-013, app/routers/runs.py:92) sends named events 'event: <type>' · web/src/lib/sse.ts · use addEventListener per EventType (see web/src/features/live-board/useBoardEvents.ts listen) or fix sse.ts
