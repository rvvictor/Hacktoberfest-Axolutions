# Plan-B recording

> **Outdated: re-record before presenting.** `plan-b.webm` was recorded on 2026-10-28,
> before the conversation flow (HACK-045 to HACK-058): it walks the old standalone tabs
> (intake, execution, spec, delivery…) and shows neither the prototype SpeedHack builds
> nor the recorded research. A person must record the current flow following
> [script.md](script.md) and replace the file; no agent has recorded or seen a newer video.
> `capture.py --screenshots-only` refreshes the screenshots without touching the video.

[Play or download the local screen recording](plan-b.webm) (outdated, see above).

This is a 3:03 silent recording of the actual application at 1280×720, with reduced
motion and `DEMO_MODE=1`. Narrate using [script.md](script.md). Download the WebM
before presenting and test playback in the presentation browser. The file is
committed alongside this document; it needs no video hosting account.

The route sequence follows the three-minute script: intake, execution, spec, board,
delivery, client, hunter, pitch, then the closing board view. The planned holds
total 180 seconds; recorded loading/capture overhead adds three seconds. Confirm
the official video limit before submission. These are independent labeled fixtures
(`demo_data: true`), not a capture of a continuous live integration run. Source
links and quality results shown in samples are not fresh verification results.
The recording has no microphone narration, real outreach, or live provider writes.

The capture utility saves real screenshots in `screenshots/` and observed route
status in `capture.json`; `screenshots.json` preserves the separate screenshot
run. `video.json` records Chromium playback metadata. Regenerate with the README
command after a fresh build.
Public video hosting and the official event video-length limit have not been
verified; the submission owner must confirm both before submitting.
