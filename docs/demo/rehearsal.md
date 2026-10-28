# Clean-clone rehearsal — 2026-10-28

Rehearsed revision: `174dcce` (integrated application base for HACK-024).
The documentation and capture utility are the HACK-024 changes on top of it.
Environment: Windows, Git Bash, Python 3.12.1, Node/npm 11.13.0 (npm version).
No provider credentials were configured or inspected. `DEMO_MODE=1`.

Created an independent checkout with no copied environment, node_modules or build:

```bash
git clone --no-hardlinks --single-branch --branch feat/hack-024 . "$TEMP/hack024-rehearsal"
uv sync --frozen --directory "$TEMP/hack024-rehearsal"
npm --prefix "$TEMP/hack024-rehearsal/web" ci --prefer-offline --no-audit --no-fund --loglevel=error
npm --prefix "$TEMP/hack024-rehearsal/web" run build
```

Observed outputs: clone completed; `Installed 61 packages in 6.74s`;
`added 69 packages in 25s`; `tsc -b && vite build`, `4597 modules transformed`,
`built in 6.51s`. This used the local package download cache. A cold network
installation time and a five-minute end-to-end setup have not been established.

From that clone, used its own `.venv/Scripts/python.exe` and FastAPI `TestClient`
against `app.main.app`, with `DEMO_MODE=1`:

| Request | Actual result |
|---|---|
| `GET /api/health` | `{'status': 'ok'}` |
| `GET /` | HTTP 200, freshly built frontend |
| `GET /api/pitch/demo-pitch` | HTTP 200 |
| `POST /api/pitch/demo-pitch/ask`, question `Alertas?` | AI disclosure, recorded expense-control explanation, `sources: ['demo:spec']`, `demo_data: true` |
| Same endpoint, `Que funciones incluye el control de gastos?` | `Soy una IA. no tengo ese dato`, empty sources, `demo_data: true` |

The browser recording uses the task worktree's fresh production build on its
assigned API port, 8340. Chromium runs with reduced motion at 1280×720; the board
screenshot shows architecture and tickets together without scrolling. Fixture
tabs are independent, not proof of a single live pipeline run. Recorded audio
is a placeholder; the rehearsal uses written Q&A.

The recording utility initially failed on hash-only navigation's absent HTTP
response, then completed its desktop recording but timed out waiting for the
mobile approval button: the final replay event occurs after the original
15-second timeout. These capture-tool issues did not alter product code; the
utility now forces document navigation and allows 25 seconds on mobile. A
screenshots-only rerun completed in 58.2 seconds: all eight routes returned HTTP
200, and all sample-result screens displayed their demo label (intake is blank).
The separate screenshot report is `screenshots.json`; the final recording report
is `capture.json`. The recording now includes the script's closing board segment
and 180 seconds of planned holds. Chromium playback verified the saved WebM:
duration 183 seconds including capture overhead, 1280×720, playing, advancing
time, no video error (`video.json`). The official event video limit is unverified.

Task Verify ran through `q bash -c` and passed: tracked secret scan, design-lint,
Ruff, `128 passed in 22.43s`, frontend lint and production build,
`PRODUCT_PASS: current adapter exited 0`. A separate `q bash .uak/bin/smoke`
also passed with exit 0. UV was installed temporarily and added
to the verifier's PATH; the README lists installed UV as a prerequisite.

Public deployment verification is pending: neither the repository, claims, nor
the repository's GitHub deployments API supplied a public URL. A request was
sent to the human through UAK. No hosting service was created or paid for.
