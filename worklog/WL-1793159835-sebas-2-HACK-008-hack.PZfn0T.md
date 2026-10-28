# worklog/WL-1793159835-sebas-2-HACK-008-hack.PZfn0T.md · HACK-008

## Live summary
- Done: voice STT/TTS/session + DEMO_MODE fixtures, 7 tests pass
- Decision: httpx direct to ElevenLabs REST (respx-mocked), not SDK; fixtures are placeholders marked demo_data
- Why: no API key yet; keeps tests offline
- Failing: -
- Commands: bash .uak/bin/q uv run pytest -q app/tests/test_voice.py
- Next: after HACK-001/002 integrate: git merge origin/main, /uak-ship; record real fixtures when key exists

## History
- 1793159835 | CLAIMED | sebas-2 | claim; next: spike one TTS call with `ELEVENLABS_VOICE_ID` and save the mp3 as a fixture.
- 1793159895 | CLAIMED | sebas-2 | checkpoint; next: after HACK-001/002 integrate: git merge origin/main, /uak-ship; record real fixtures when key exists
