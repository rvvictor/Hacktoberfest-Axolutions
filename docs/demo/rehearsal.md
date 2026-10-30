# Clean-clone rehearsals

## 2026-10-29 · `main` at `bca7672` (conversation flow, kit 5.8.0)

Environment: macOS (Darwin 24.6.0), Python 3.12.4, Node v24.21.0. No `.env`, no provider
keys: `DEMO_MODE` defaults to true. Fresh clone of `origin/main` in an empty directory.

```bash
git clone https://github.com/rvvictor/Hacktoberfest-Axolutions.git rehearsal && cd rehearsal
uv sync --frozen && npm --prefix web ci && npm --prefix web run build
```

| Check | Actual result |
|---|---|
| Clone + README setup + build | done in 8 s (uv and npm caches already warm on this machine; a cold install was not timed) |
| `bash .uak/bin/q bash -c 'test -s README.md && test -s docs/demo/script.md && bash .uak/bin/smoke'` | `OK exit=0 46s · PRODUCT_PASS: current adapter exited 0.` |
| `UAK_PORT=8645 uv run python e2e/judge_path.py` | `OK exit=0 19s · PASS judge path run=run_d0180b98 steps=8 demo_data=true` (includes no overlapping board labels and no page scroll at 1280×720) |
| Machine time to the wow (API, `DEMO_MODE=1`, default `DEMO_SPEED=2`) | 1.8 s to the questions, 2.6 s answers → plan, 4.8 s approval 1 → board and tasks: **9.2 s** |
| Pitch Q&A on that run | “¿Cómo funcionan las alertas?” → quotes “Funcionalidad del MVP: Alertas automatizadas…”, source `spec:v1`; “¿De qué trata el proyecto?” → quotes “Problema: La gestión de gastos corporativos…”, source `spec:v1` |

Not rehearsed here: a human walking the script with a stopwatch, and the plan-B video,
which is outdated and must be re-recorded (`plan-b.md`).

## 2026-10-28 · HACK-024 base `174dcce`

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

Public deployment verified on 2026-10-28 at https://speedhack.onrender.com using
`.venv/Scripts/python.exe docs/demo/check-public.py`.
Chromium ran at 1280×720 with reduced motion. `GET /api/health` returned HTTP 200
and `{"status":"ok"}`. Intake, the completed recorded board, and pitch returned
HTTP 200; board and pitch displayed their demo labels. Written pitch Q&A completed
in the browser. `POST /api/pitch/demo-pitch/ask` with `Alertas?` returned HTTP 200,
the recorded expense-control answer, `sources: ["demo:spec"]`, and `demo_data: true`.
The machine-readable result is `public-check.json`; `screenshots/public-*.png`
are actual captures of that deployment. This verifies recorded mode only.
Render's free tier sleeps after 15 minutes idle; judges should allow about one
minute for the first load. Hosting configuration and autodeploy on `main` were
reported by the deployment owner; no hosting service was created or paid for here.

After merging current `main` and adding the public URL, the exact task Verify
through `q` passed again: `OK exit=0 427s · PRODUCT_PASS: current adapter exited 0.`
Its log recorded `SECRET_SCAN_PASS files=465 mode=tracked`,
`DESIGN_LINT_PASS files=30 ui=web/src/lib/ui`, Ruff `All checks passed!`,
`128 passed in 25.45s`, frontend lint, and a fresh build completed in 7.06 seconds.
