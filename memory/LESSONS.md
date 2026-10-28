# Lessons (uak learn)

Append-only. Format: - N | epoch | agent | task | paths | text. `uak recall` and `uak next` show the ones for your paths.

- 1 | 1793164317 | dylan-1 | HACK-016 | web/src/features/live-board/ | lib/sse.ts subscribe() uses onmessage but runs router (HACK-013, app/routers/runs.py:92) sends named events 'event: <type>' · web/src/lib/sse.ts · use addEventListener per EventType (see web/src/features/live-board/useBoardEvents.ts listen) or fix sse.ts
- 2 | 1793164527 | victor-1 | - | * | smoke runs ruff on all of app/; branches started before HACK-001 fail the merge gate with UP045/UP017/RUF100 · app/ · git merge origin/main && uv run ruff check --fix app before uak done
