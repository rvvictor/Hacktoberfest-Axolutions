"""Manual browser verification: uv run python web/src/features/pitch/check_browser.py."""

import io
import json
import os
import wave
from pathlib import Path

from playwright.sync_api import expect, sync_playwright

PORT = next(
    line.split("=", 1)[1].strip()
    for line in Path(".uak-env").read_text().splitlines()
    if line.startswith("UAK_PORT=")
)
OUT = Path(os.environ["TEMP"]) / "hack-019-browser"
OUT.mkdir(exist_ok=True)
wav = io.BytesIO()
with wave.open(wav, "wb") as recording:
    recording.setnchannels(1)
    recording.setsampwidth(2)
    recording.setframerate(16000)
    recording.writeframes(b"\0\0" * 1600)

with sync_playwright() as p:
    browser = p.chromium.launch(
        args=["--use-fake-ui-for-media-stream", "--use-fake-device-for-media-stream"]
    )
    context = browser.new_context(
        permissions=["microphone"],
        reduced_motion="reduce",
        viewport={"width": 1280, "height": 720},
    )
    page = context.new_page()
    errors = []
    page.on("pageerror", lambda error: errors.append(str(error)))
    page.goto(f"http://127.0.0.1:{PORT}/#/pitch")
    page.wait_for_load_state("networkidle")
    # HACK-066: a cover, then the recorded deck of the demo case; "Exportar PDF" prints one page per slide.
    expect(page.locator(".pitch-cover h2")).to_have_text("SaaS de control de gastos corporativos")
    page.get_by_role("button", name="Siguiente", exact=True).click()
    expect(page.get_by_role("heading", name="El Problema", exact=True)).to_be_visible()
    page.emulate_media(media="print")
    assert page.locator(".pitch-slide:visible").count() == page.locator(".pitch-slide").count() == 7
    page.pdf(path=str(OUT / "pitch.pdf"))
    page.emulate_media(media="screen")
    page.get_by_role("button", name="Anterior", exact=True).click()
    page.get_by_label("Tu pregunta", exact=True).fill("¿Cómo funcionan las alertas?")
    page.get_by_role("button", name="Preguntar", exact=True).click()
    expect(page.locator(".pitch-answers")).to_contain_text("Soy una IA.")
    expect(page.locator(".pitch-answers")).to_contain_text("demo:spec")
    page.screenshot(path=str(OUT / "pitch-1280.png"))
    page.set_viewport_size({"width": 390, "height": 844})
    page.screenshot(path=str(OUT / "pitch-390.png"), full_page=True)
    assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
    page.set_viewport_size({"width": 1280, "height": 720})
    page.get_by_label("Tu pregunta", exact=True).fill("¿Quién ganó el mundial?")
    page.get_by_role("button", name="Preguntar", exact=True).click()
    expect(page.locator(".pitch-answers article").first).to_contain_text(
        "no tengo ese dato"
    )
    # Voice contracts are explicitly simulated until HACK-008 integrates.
    spoken = []
    page.route(
        "**/api/voice/stt",
        lambda route: route.fulfill(
            json={"text": "¿Cómo funcionan las alertas?", "demo_data": True}
        ),
    )

    def tts(route):
        spoken.append(route.request.post_data_json["text"])
        route.fulfill(body=wav.getvalue(), content_type="audio/wav")

    page.route("**/api/voice/tts", tts)
    page.get_by_role("button", name="Hablar", exact=True).click()
    expect(page.get_by_role("button", name="Terminar y enviar")).to_be_visible()
    page.get_by_role("button", name="Terminar y enviar").click()
    expect(page.locator(".pitch-answers article")).to_have_count(3)
    page.wait_for_function(
        "document.querySelectorAll('.pitch-answers article').length === 3"
    )
    expect(page.get_by_role("button", name="Hablar", exact=True)).to_be_enabled()
    assert spoken and spoken[0].startswith("Soy una IA.")
    # Delayed answers are invalidated when a new run is opened.
    pending = []
    page.route("**/api/pitch/demo-pitch/ask", lambda route: pending.append(route))
    page.get_by_label("Tu pregunta", exact=True).fill("alertas")
    page.get_by_role("button", name="Preguntar", exact=True).click()
    page.wait_for_timeout(100)
    page.locator(".pitch-settings summary").click()
    page.get_by_label("Ejecución", exact=True).fill("missing-run")
    page.get_by_role("button", name="Abrir", exact=True).click()
    expect(page.get_by_role("alert")).to_be_visible()
    if pending:
        pending[0].fulfill(
            json={
                "question": "alertas",
                "answer": "Respuesta anterior",
                "sources": [],
                "demo_data": True,
            }
        )
    page.get_by_role("button", name="Ver demostración", exact=True).click()
    expect(page.get_by_role("heading", name="El proyecto", exact=True)).to_be_visible()
    expect(page.locator(".pitch-answers")).not_to_contain_text("Respuesta anterior")
    page.unroute("**/api/pitch/demo-pitch/ask")
    page.unroute("**/api/voice/stt")
    page.route("**/api/voice/stt", lambda route: route.fulfill(status=503))
    page.get_by_role("button", name="Hablar", exact=True).click()
    page.get_by_role("button", name="Terminar y enviar").click()
    expect(page.get_by_role("alert")).to_contain_text("No pudimos transcribir")
    # A late transcript must not ask a question in a different run.
    page.unroute("**/api/voice/stt")
    late_stt = []
    page.route("**/api/voice/stt", lambda route: late_stt.append(route))
    page.get_by_role("button", name="Hablar", exact=True).click()
    page.get_by_role("button", name="Terminar y enviar").click()
    expect(page.get_by_role("status")).to_contain_text("Transcribiendo")
    page.get_by_label("Ejecución", exact=True).fill("other-run")
    page.get_by_role("button", name="Abrir", exact=True).click()
    expect(page.get_by_role("alert")).to_be_visible()
    assert late_stt
    late_stt[0].fulfill(json={"text": "alertas", "demo_data": True})
    expect(page.locator(".pitch-answers article")).to_have_count(0)
    page.get_by_role("button", name="Ver demostración", exact=True).click()
    expect(page.get_by_role("heading", name="El proyecto", exact=True)).to_be_visible()
    # TTS failures preserve the written answer and explain the fallback.
    page.unroute("**/api/voice/stt")
    page.route("**/api/voice/stt", lambda route: route.fulfill(json={"text": "alertas", "demo_data": True}))
    page.unroute("**/api/voice/tts")
    page.route("**/api/voice/tts", lambda route: route.fulfill(status=503))
    page.get_by_role("button", name="Hablar", exact=True).click()
    page.get_by_role("button", name="Terminar y enviar").click()
    expect(page.get_by_role("alert")).to_contain_text("La voz no está disponible")
    expect(page.locator(".pitch-answers article")).to_have_count(1)
    assert not errors, errors
    browser.close()
print(json.dumps({"browser": "PASS", "demo_data_voice": True, "artifacts": str(OUT)}))
