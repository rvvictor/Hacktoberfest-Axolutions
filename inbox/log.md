# Agent messages

Append-only; use bash .uak/bin/uak msg / inbox. Format: - N | epoch | from | to | kind | task | text

- 1 | 1793158501 | victor-2 | all | contract | HACK-002 | HACK-002 schemas in app/schemas/ (run.py, content.py), TS in web/src/lib/types.ts; StageEvent.ts = seconds since run start; fixture app/fixtures/demo/run.jsonl
- 2 | 1793158532 | victor-2 | agent:victor-1 | review | HACK-002 | HACK-002 ready for review (your turn by rotation): https://github.com/rvvictor/Hacktoberfest-Axolutions/pull/1 (SHA 82fa2e963c54385720f5dcb8fd3daaa9ac9bbafd). /uak-review HACK-002; if you can't, reply and any free agent takes it (uak next shows it).
