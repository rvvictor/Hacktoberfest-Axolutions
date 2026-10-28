# Memory spike

`local_roundtrip.json` is a recording produced by the actual local keyword
implementation, with `demo_data: true`. It is **not** a Backboard recording.
No Backboard key was configured and no pre-existing recording was available.
HACK-009 acceptance criterion 3 remains pending until a live round trip is saved.

API documentation checked on 2026-10-27:

- https://docs.backboard.io/api-reference/assistants/create
- https://docs.backboard.io/api-reference/assistants/create-thread
- https://docs.backboard.io/api-reference/memories/add
- https://docs.backboard.io/api-reference/memories/search

The adapter creates an assistant per run and a thread, then adds memories with
run/kind/source metadata and searches the assistant's memories. Search responses
omit metadata, so the adapter resolves returned IDs against locally cached records
to preserve provenance; unknown IDs are ignored. Transport tests use test doubles,
not live provider evidence. Requests have an 8-second timeout and no automatic
retry of creates/writes.

Usage: `remember(run_id, kind, text, source)` returns a passage dict;
`recall(run_id, query, k=5)` returns passage dicts containing
`run_id`, `kind`, `text`, `source`, `demo_data`. Supported k is 0–50.
Module functions share one service instance; isolated consumers can instantiate
`MemoryService`. No API key or `DEMO_MODE=true` selects the local keyword index.
Provider errors fall back to that index and label results `demo_data: true`.
Empty/unmatched queries return an empty list, never an invented answer.

This is a process-local cache, never the spec of record. HACK-013 must rehydrate
it from its store by calling `remember` after restart. Run isolation is enforced
by separate assistants and local indexes. Identical run/kind/text/source writes
are deduplicated. Source strings should be stage IDs, URLs, or decision IDs.
Calls are synchronous; async routes should offload them to a worker thread.

To record the live spike, configure the key through the secret environment,
construct `MemoryService(demo_mode=False)`, remember a non-sensitive passage,
then recall it. Save sanitized request/response bodies and provenance, excluding
headers and credentials. Mark any replay fixture `demo_data: true` and explicitly
record whether the underlying provider call was live. A test double is not a
substitute for the missing live recording.
