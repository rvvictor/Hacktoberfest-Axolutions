# Lessons (uak learn)

Append-only. Format: - N | epoch | agent | task | paths | text. `uak recall` and `uak next` show the ones for your paths.

- 1 | 1793164317 | dylan-1 | HACK-016 | web/src/features/live-board/ | lib/sse.ts subscribe() uses onmessage but runs router (HACK-013, app/routers/runs.py:92) sends named events 'event: <type>' · web/src/lib/sse.ts · use addEventListener per EventType (see web/src/features/live-board/useBoardEvents.ts listen) or fix sse.ts
- 2 | 1793164527 | victor-1 | - | * | smoke runs ruff on all of app/; branches started before HACK-001 fail the merge gate with UP045/UP017/RUF100 · app/ · git merge origin/main && uv run ruff check --fix app before uak done
- 3 | 1793194744 | victor-2 | HACK-027 | web/src/features/run/,web/src/features/live-board/,web/src/features/delivery/,web/src/features/intake/,web/src/features/pitch/ | pitch deck empty and Q&A without sources for real runs: app/services/pitch.py only has data for run demo-pitch or memory passages · app/services/pitch.py · check the pipeline writes memory per run_id
- 4 | 1793406765 | victor-3 | HACK-072 | app/services/pitch.py,app/services/voice.py,app/config.py,app/tests/test_narration_spend.py | test_voice.py live /api/voice/tts tests use the real DATA_DIR, so the daily ELEVENLABS_DAILY_CHARS counter lands in data/voice/chars.json and grows every local run · app/tests/test_voice.py · add an autouse monkeypatch of settings.DATA_DIR to tmp_path there
