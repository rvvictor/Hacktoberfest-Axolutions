# ADR 0001 · Quality checks on Render: do not add a browser to the runtime image

Status: proposed (HACK-069) · Decider: the responsible human · Measured 2026-10-29 on a Mac, not on Render.

## Context
`app/services/quality.py` runs four checks on the single HTML page SpeedHack generates:
`lint` and `secrets` are regexes. `build` is `node --check` on each inline script. `smoke` opens the
page in Playwright Chromium, isolated and with no network.

The runtime image is `python:3.12-slim` with no Node and no browser, so on
https://speedhack.onrender.com only `lint` and `secrets` run. `build` and `smoke` come back as
"not run" (seen on `run_f5460ad2`). They are never reported as passed.

The service is on Render's `free` plan: 0.1 CPU, 512 MB RAM
([compute plans](https://render.com/docs/compute-plans)). Other web plans on that page:
`starter` 0.5 CPU / 512 MB, `standard` 1 CPU / 2 GB, `pro` 2 CPU / 4 GB.

## Measurements
All on macOS arm64 with Node v26.9.0 and Playwright Chromium 1248, over
`app/fixtures/generator/speedhack/index.html` (19,964 bytes). All four checks passed.

| What | Result |
|---|---|
| `node --check` of the page's scripts, max resident memory | 41 MB, 0.22 s |
| `check_app` end to end (Python + node + Chromium), peak of the summed RSS of the process tree, 3 runs | 435, 455, 453 MiB across 6 processes |
| Python importing `app.main` (the server, before serving anything), max RSS | 109 MiB |
| Chromium on disk: `chromium_headless_shell` / full `chromium` | 203 MB / 366 MB |

## Not measured
- **Image size.** There is no Docker on the machine that did this, so `docker build` was not run and no image size is claimed. Chromium's Linux x64 build differs from the arm64 one above.
- **Memory on Linux.** The sums above add RSS per process, which counts shared pages more than once, so they overestimate. They also come from macOS, not from a container with a 512 MB limit.
- **CPU time on 0.1 CPU.** `check_app` took 1.1 s here; on a tenth of a core it will be much slower, and the free plan sleeps after 15 minutes idle.

## Decision
Do not add Chromium (or Playwright) to the runtime image on the `free` or `starter` plans.

Reason: the browser tree alone peaked near 450 MiB here, and the server needs about 110 MiB before it
serves a request. That is above the 512 MB limit even allowing for the overestimate, with no margin
for the pipeline stages running at the same time.

Keep `build` and `smoke` reported as "not run" on Render, as now. They do run wherever Node and a
browser exist: the four checks passed in the measurements above.

## Alternatives
1. **Node only.** `node --check` needed 41 MB here, so `build` could run on Render by adding Node to the image. Not done: the image size is unmeasured and `docker build` was not run, so it is not shown to fit. Do it only after a real `docker build` and a deploy check.
2. **A larger plan.** `standard` has 2 GB and would hold the browser tree with room to spare. It costs money, so it needs the responsible human's explicit authorization (AGENTS.md §1.3); nothing here changes the plan.
3. **Run `smoke` elsewhere.** A separate worker, or GitHub Actions on the generated page, keeps the web service small.

## Consequences
The Render quality report stays at two real checks plus two honest "not run". The pitch must not
claim four checks ran on Render.
