"""Judge path end to end (HACK-029): intake, 9-stage run, approvals 1-3, board, delivery, pitch Q&A.

Verify: uv run python e2e/judge_path.py
Builds web/ fresh, starts the API with DEMO_MODE=1 on $UAK_PORT (or the .uak-env value) and serves web/dist
from it, then drives headless Chromium with reduced motion. Screenshots go to e2e/out/.
Exits 1 with "FAIL step=<name>: <reason>" on the first failed step.
Not covered: hunter and client modes (step 5, P1), the live Miro embed and the Lovable preview.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import signal
import socket
import subprocess
import sys
import time
import urllib.request
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from pathlib import Path

from playwright.sync_api import Error as PlaywrightError
from playwright.sync_api import Page, expect, sync_playwright

ROOT = Path(__file__).resolve().parents[1]
WEB = ROOT / "web"
OUT = Path(__file__).resolve().parent / "out"
T = 60_000  # ms: a fixture run takes about 24 s at DEMO_SPEED=2
ANSWER = "Sí: varias empresas, roles de aprobador y alertas por correo."
FAKE_MEDIA = [
    "--use-fake-ui-for-media-stream",
    "--use-fake-device-for-media-stream",
    "--autoplay-policy=no-user-gesture-required",
]


class Fail(Exception):
    pass


def port() -> int:
    value = os.environ.get("UAK_PORT", "")
    env_file = ROOT / ".uak-env"
    if not value and env_file.is_file():
        for line in env_file.read_text().splitlines():
            if line.startswith("UAK_PORT="):
                value = line.split("=", 1)[1].strip()
    if not value.isdigit():
        raise Fail("setup: no UAK_PORT (set it, or run from a uak worktree with .uak-env)")
    return int(value)


def check_port_free(p: int) -> None:
    with socket.socket() as s:
        if s.connect_ex(("127.0.0.1", p)) == 0:
            raise Fail(f"setup: port {p} is already in use; run `bash .uak/bin/wt stop` and retry")


def run_logged(name: str, cmd: list[str], cwd: Path, log: Path) -> None:
    with log.open("w") as fh:
        code = subprocess.run(cmd, cwd=cwd, stdout=fh, stderr=subprocess.STDOUT, check=False).returncode
    if code:
        raise Fail(f"setup: {name} exited {code}; see {log}")


def build_web() -> None:
    if not (WEB / "node_modules").is_dir():
        run_logged("npm ci", ["npm", "ci"], WEB, OUT / "npm-ci.log")
    shutil.rmtree(WEB / "dist", ignore_errors=True)  # a fresh build: a stale dist proves nothing
    run_logged("npm run build", ["npm", "run", "build"], WEB, OUT / "build.log")


def install_chromium() -> None:
    run_logged(
        "playwright install chromium",
        [sys.executable, "-m", "playwright", "install", "chromium"],
        ROOT,
        OUT / "playwright-install.log",
    )


def start_api(p: int) -> subprocess.Popen:
    data = OUT / "data"
    shutil.rmtree(data, ignore_errors=True)
    env = {**os.environ, "DEMO_MODE": "1", "DATA_DIR": str(data)}
    log = (OUT / "api.log").open("w")
    proc = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", str(p)],
        cwd=ROOT,
        env=env,
        stdout=log,
        stderr=subprocess.STDOUT,
        start_new_session=True,
    )
    for _ in range(100):
        if proc.poll() is not None:
            raise Fail(f"setup: the API exited with {proc.returncode}; see {OUT / 'api.log'}")
        try:
            with urllib.request.urlopen(f"http://127.0.0.1:{p}/api/health", timeout=2) as r:
                if r.status == 200:
                    return proc
        except OSError:
            time.sleep(0.3)
    stop_api(proc)
    raise Fail(f"setup: the API did not answer /api/health on {p}")


def stop_api(proc: subprocess.Popen) -> None:
    if proc.poll() is not None:
        return
    os.killpg(proc.pid, signal.SIGTERM)
    try:
        proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        os.killpg(proc.pid, signal.SIGKILL)


def get_run(p: int, run_id: str) -> dict:
    with urllib.request.urlopen(f"http://127.0.0.1:{p}/api/runs/{run_id}", timeout=10) as r:
        return json.loads(r.read())


def wait_run(p: int, run_id: str, ok: Callable[[dict], bool], what: str) -> None:
    deadline = time.time() + T / 1000
    run: dict = {}
    while time.time() < deadline:
        run = get_run(p, run_id)
        if ok(run):
            return
        time.sleep(0.3)
    raise Fail(f"{what}: timed out (status={run.get('status')}, awaiting={run.get('awaiting')})")


def go(page: Page, base: str, run_id: str, view: str) -> None:
    # The screens read `?run=` before the hash, the form intake writes.
    page.goto(f"{base}/?run={run_id}#/{view}")


@contextmanager
def step(page: Page, name: str, shots: list[str]) -> Iterator[None]:
    print(f"STEP {name}", flush=True)
    try:
        yield
    except Exception as exc:
        slug = re.sub(r"\W+", "-", name).strip("-")
        try:
            page.screenshot(path=str(OUT / f"failure-{slug}.png"), full_page=True)
        except PlaywrightError as shot_exc:
            print(f"WARN no failure screenshot: {shot_exc}", flush=True)
        first = (str(exc).splitlines() or [type(exc).__name__])[0][:400]
        raise Fail(f"step={name}: {first}") from exc
    shots.append(name)


# Pairs of visible text labels on the Miro mirror whose boxes intersect (1 px tolerance).
BOARD_OVERLAPS = """() => {
  const els = [...document.querySelectorAll('.lb-canvas *')]
    .filter((e) => e.children.length === 0 && e.textContent.trim() && e.getClientRects().length);
  const boxes = els.map((e) => [e.textContent.trim().slice(0, 30), e.getBoundingClientRect()]);
  const out = [];
  for (let i = 0; i < boxes.length; i++) for (let j = i + 1; j < boxes.length; j++) {
    const [ta, a] = boxes[i], [tb, b] = boxes[j];
    if (a.left < b.right - 1 && b.left < a.right - 1 && a.top < b.bottom - 1 && b.top < a.bottom - 1) out.push([ta, tb]);
  }
  return out;
}"""


def shot(page: Page, name: str) -> None:
    page.screenshot(path=str(OUT / f"{name}.png"), full_page=True)


def decide(page: Page, p: int, run_id: str, number: int, confirm: str) -> None:
    """Approve gate `number` from its card in the conversation, the way a judge does."""
    wait_run(p, run_id, lambda r: r.get("awaiting") == f"approval:{number}", f"approval {number} gate")
    approve = page.get_by_role("button", name="Sí, sigamos", exact=True)
    expect(approve).to_be_enabled(timeout=T)
    with page.expect_response(lambda r: f"/approvals/{number}" in r.url) as decision:
        approve.click()
    if decision.value.status != 200:
        raise Fail(f"approval {number} returned {decision.value.status}")
    wait_run(p, run_id, lambda r: r.get("awaiting") != f"approval:{number}", f"approval {number} accepted")
    expect(page.get_by_text(confirm).first).to_be_visible(timeout=T)


def judge(page: Page, base: str, p: int, shots: list[str]) -> str:
    # 1. Intake, the first turn: dictation (the STT fixture in DEMO_MODE), then typing, then POST /api/projects,
    #    which hands off to the conversation at ?run=ID#/project.
    page.goto(f"{base}/#/intake")
    idea = page.get_by_label("Tu idea")
    with step(page, "1 intake: dictate", shots):
        page.get_by_role("radio", name=re.compile("Soy desarrollador")).click()
        page.get_by_role("button", name="Dictar por voz", exact=True).click()
        stop = page.get_by_role("button", name="Detener y transcribir", exact=True)
        expect(stop).to_be_visible(timeout=T)
        page.wait_for_timeout(1500)
        stop.click()
        expect(idea).to_have_value(re.compile(r"\S"), timeout=T)
        shot(page, "01-intake-dictated")
    with step(page, "1 intake: type and start", shots):
        idea.click()
        idea.press("End")
        idea.press_sequentially(" Para el equipo de finanzas.")
        with page.expect_response(lambda r: r.url.endswith("/api/projects") and r.request.method == "POST") as created:
            page.get_by_role("button", name="Empezar", exact=True).click()
        if created.value.status != 201:
            raise Fail(f"POST /api/projects returned {created.value.status}")
        # The intake navigates to the conversation right away, so the run id is read from that URL.
        page.wait_for_url(lambda u: "run=" in u and "#/project" in u, timeout=T)
        match = re.search(r"[?&]run=([^&#]+)", page.url)
        if not match:
            raise Fail(f"no run id in {page.url}")
        run_id = match.group(1)

    # 2. The questions arrive one at a time in the conversation; the last answer posts them all.
    with step(page, "2 questions: answer one at a time", shots):
        wait_run(p, run_id, lambda r: r.get("awaiting") == "answers", "stage 2 waiting for answers")
        reply = page.get_by_label("Tu respuesta")
        expect(reply).to_be_visible(timeout=T)
        shot(page, "02-first-question")
        answered = 0
        while True:
            last = page.get_by_role("button", name="Responder y seguir", exact=True)
            reply.fill(ANSWER)
            answered += 1
            if last.count():
                with page.expect_response(lambda r: r.url.endswith("/answers") and r.request.method == "POST") as sent:
                    last.click()
                if sent.value.status != 200:
                    raise Fail(f"POST answers returned {sent.value.status}")
                break
            page.get_by_role("button", name="Responder", exact=True).click()
            if answered > 10:
                raise Fail("more than 10 questions: the conversation never offered 'Responder y seguir'")
        wait_run(p, run_id, lambda r: r.get("awaiting") != "answers", "answers accepted")

    # 3. Research and the plan; approval 1 on the plan card.
    with step(page, "3 plan: sources and approval 1", shots):
        expect(page.get_by_text("Qué vamos a construir", exact=True)).to_be_visible(timeout=T)
        shot(page, "03-plan")
        decide(page, p, run_id, 1, "Aprobado. Seguimos.")

    # 4. Miro and Linear fill from the same plan; approval 2 on the tasks card. The board view is the wow.
    with step(page, "4 board and tasks: approval 2", shots):
        expect(page.get_by_text(re.compile(r"^Dibujé la arquitectura en Miro"))).to_be_visible(timeout=T)
        expect(page.get_by_text(re.compile(r"^Creé \d+ tareas en Linear"))).to_be_visible(timeout=T)
        shot(page, "04-board-and-tasks")
        decide(page, p, run_id, 2, "Aprobado. Seguimos.")
        go(page, base, run_id, "live-board")
        expect(page.get_by_text(re.compile(r"^[1-9]\d* elementos$"))).to_be_visible(timeout=T)
        # The wow is judged on a projector: 1280×720, no page scroll, no label on top of another.
        page.set_viewport_size({"width": 1280, "height": 720})
        page.wait_for_timeout(500)
        overlaps = page.evaluate(BOARD_OVERLAPS)
        if overlaps:
            raise AssertionError(f"board labels overlap at 1280x720: {overlaps[:3]}")
        scroll = page.evaluate("document.documentElement.scrollHeight")
        if scroll > 720:
            raise AssertionError(f"the wow needs page scroll at 1280x720 (scrollHeight {scroll})")
        shot(page, "05-board-wow")
        page.set_viewport_size({"width": 1280, "height": 800})
        go(page, base, run_id, "project")

    # 5. Prototype and its review; approval 3 on the prototype card.
    with step(page, "5 prototype: approval 3", shots):
        expect(page.get_by_role("link", name="Abrir el prototipo")).to_be_visible(timeout=T)
        shot(page, "06-prototype")
        decide(page, p, run_id, 3, "Aprobado. Seguimos.")

    # 6. The run reaches its final state: the pitch card in the conversation, 9 of 9 in the detail view.
    with step(page, "6 run: final state", shots):
        wait_run(p, run_id, lambda r: r.get("status") == "done", "run status done")
        expect(page.get_by_role("link", name="Ir a la sala de pitch")).to_be_visible(timeout=T)
        shot(page, "07-project-done")
        go(page, base, run_id, "run")
        expect(page.get_by_text("Ejecución terminada.", exact=True)).to_be_visible(timeout=T)
        expect(page.get_by_text("9/9", exact=True)).to_be_visible(timeout=T)
        # The finished run's board: the server closes its event stream, and the view must not choke on that.
        go(page, base, run_id, "live-board")
        expect(page.get_by_text(re.compile(r"^[1-9]\d* elementos$"))).to_be_visible(timeout=T)
        page.wait_for_timeout(3000)

    # 7. Pitch room: the deck and one question answered with its sources.
    with step(page, "7 pitch: deck and Q&A", shots):
        go(page, base, run_id, "pitch")
        expect(page.get_by_role("heading", name="Sala de pitch")).to_be_visible(timeout=T)
        expect(page.locator(".pitch-slide h2").first).to_be_visible(timeout=T)
        shot(page, "08-pitch-deck")
        page.get_by_label("Tu pregunta", exact=True).fill("¿Cómo funcionan las alertas?")
        with page.expect_response(lambda r: "/ask" in r.url and r.request.method == "POST") as asked:
            page.get_by_role("button", name="Preguntar", exact=True).click()
        if asked.value.status != 200:
            raise Fail(f"POST /ask returned {asked.value.status}")
        article = page.locator(".pitch-answers article").first
        expect(article).to_contain_text("Soy una IA.", timeout=T)
        sources = article.locator("ul[aria-label='Fuentes'] li")
        if sources.count() == 0:
            raise Fail("the answer has no sources")
        shot(page, "09-pitch-answer")
    return run_id


def main() -> int:
    p = port()
    OUT.mkdir(parents=True, exist_ok=True)
    check_port_free(p)
    shots: list[str] = []
    errors: list[str] = []
    proc: subprocess.Popen | None = None
    try:
        build_web()
        install_chromium()
        proc = start_api(p)
        base = f"http://127.0.0.1:{p}"
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True, args=FAKE_MEDIA)
            context = browser.new_context(
                permissions=["microphone"],
                reduced_motion="reduce",
                viewport={"width": 1280, "height": 800},
            )
            page = context.new_page()
            page.on("pageerror", lambda e: errors.append(f"{e} @ {page.url}"))
            page.on("response", lambda r: errors.append(f"HTTP {r.status} {r.url}") if r.status >= 500 else None)
            run_id = judge(page, base, p, shots)
            browser.close()
    except Fail as exc:
        print(f"FAIL {exc}", flush=True)
        print(f"screenshots: {OUT}", flush=True)
        return 1
    finally:
        if proc is not None:
            stop_api(proc)
    # The run-screen JSON.parse(undefined) bug once allowlisted here was fixed in HACK-034: every error fails now.
    if errors:
        print(f"FAIL page or server errors: {errors[:5]}", flush=True)
        return 1
    print(
        f"PASS judge path run={run_id} steps={len(shots)} demo_data=true screenshots={OUT}",
        flush=True,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
