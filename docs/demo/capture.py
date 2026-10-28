"""Capture the actual labeled fixture UI; run after building and starting FastAPI."""

import argparse
import json
import time
from pathlib import Path

from playwright.sync_api import sync_playwright


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", required=True, help="Worktree API origin")
    parser.add_argument("--screenshots-only", action="store_true")
    args = parser.parse_args()
    out = Path(__file__).resolve().parent
    (out / "screenshots").mkdir(exist_ok=True)
    started = time.monotonic()
    results = []
    with sync_playwright() as p:
        browser = p.chromium.launch()
        video_options = {} if args.screenshots_only else {
            "record_video_dir": str(out / "recordings"),
            "record_video_size": {"width": 1280, "height": 720},
        }
        context = browser.new_context(
            viewport={"width": 1280, "height": 720},
            reduced_motion="reduce",
            **video_options,
        )
        page = context.new_page()
        for route, seconds in [
            ("intake", 20), ("run", 20), ("spec", 15), ("live-board", 25),
            ("delivery", 25), ("client", 10), ("hunter", 10), ("pitch", 40),
            ("live-board", 15),
        ]:
            stage_start = time.monotonic()
            response = page.goto(f"{args.base}/?capture={route}#/{route}")
            page.wait_for_load_state("networkidle")
            page.wait_for_timeout(2500)
            if route == "live-board":
                page.get_by_text("Aprobar diseño", exact=True).wait_for(timeout=25000)
            if route == "pitch":
                field = page.locator("textarea").first
                if field.count():
                    field.fill("¿Qué funciones incluye el control de gastos?")
                    page.get_by_role("button", name="Preguntar", exact=True).click()
                    page.wait_for_timeout(2000)
            page.screenshot(path=str(out / "screenshots" / f"{route}.png"))
            body = page.inner_text("body")
            results.append({"route": route, "http": response.status if response else None, "demo_label": "demo_data" in body or "Datos de demostración" in body})
            remaining = seconds - (time.monotonic() - stage_start)
            if remaining > 0 and not args.screenshots_only:
                page.wait_for_timeout(remaining * 1000)
        video = page.video
        context.close()
        if video:
            video.save_as(str(out / "plan-b.webm"))
            video.delete()
        mobile = browser.new_context(viewport={"width": 390, "height": 844}, reduced_motion="reduce")
        small = mobile.new_page()
        small.goto(f"{args.base}/#/live-board")
        small.get_by_text("Aprobar diseño", exact=True).wait_for(state="attached", timeout=25000)
        small.screenshot(path=str(out / "screenshots" / "live-board-mobile.png"))
        mobile.close()
        browser.close()
    report = {"demo_data": True, "screenshots_only": args.screenshots_only, "elapsed_seconds": round(time.monotonic() - started, 1), "routes": results}
    report_name = "screenshots.json" if args.screenshots_only else "capture.json"
    (out / report_name).write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report))


if __name__ == "__main__":
    main()
