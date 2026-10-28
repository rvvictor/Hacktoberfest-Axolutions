"""Verify the deployed recorded demo without provider credentials."""

import json
from pathlib import Path

from playwright.sync_api import sync_playwright


origin = "https://speedhack.onrender.com"
out = Path(__file__).resolve().parent
with sync_playwright() as p:
    browser = p.chromium.launch()
    context = browser.new_context(
        viewport={"width": 1280, "height": 720}, reduced_motion="reduce"
    )
    page = context.new_page()
    health = context.request.get(f"{origin}/api/health", timeout=120000)
    assert health.status == 200, health.status
    assert health.json() == {"status": "ok"}, health.text()
    print("GET /api/health: 200 " + health.text(), flush=True)
    results = []
    for route in ["intake", "live-board", "pitch"]:
        response = page.goto(f"{origin}/?verify={route}#/{route}", timeout=120000)
        assert response and response.status == 200
        page.wait_for_load_state("networkidle")
        if route == "live-board":
            page.get_by_text("Aprobar diseño", exact=True).wait_for(timeout=30000)
        elif route == "pitch":
            page.locator("textarea").first.fill("Alertas?")
            page.get_by_role("button", name="Preguntar", exact=True).click()
            page.get_by_text("Soy una IA", exact=False).last.wait_for(timeout=30000)
        body = page.inner_text("body")
        labeled = "demo_data" in body or "Datos de demostración" in body
        if route != "intake":
            assert labeled, body
        page.screenshot(path=str(out / "screenshots" / f"public-{route}.png"))
        results.append({"route": route, "http": response.status, "demo_label": labeled})
        print(json.dumps(results[-1]), flush=True)
    answer = context.request.post(
        f"{origin}/api/pitch/demo-pitch/ask", data={"question": "Alertas?"}
    )
    assert answer.status == 200, answer.text()
    payload = answer.json()
    assert payload["demo_data"] is True, payload
    print("POST pitch ask: " + json.dumps(payload, ensure_ascii=False), flush=True)
    (out / "public-check.json").write_text(
        json.dumps({"origin": origin, "health": health.json(), "routes": results,
                    "pitch_answer": payload}, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    browser.close()
