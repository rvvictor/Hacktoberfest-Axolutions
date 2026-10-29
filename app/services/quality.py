"""Quality gate for a generated repo: returns a QualityReport with each check's status.

In-process checks: rls. The rest (build, lint, gitleaks, npm audit, smoke) run in the
generated repo's CI from quality/generated-repo-ci.yml, so they are named in `details`
instead of being reported as passed.

`check_app` gates the single page SpeedHack generates itself: build, lint, secrets and smoke really
run on that file. A check whose tool is missing here (node, a browser) is left out of `checks` and
named in `details` as not run: it is never reported as passed.
"""

from __future__ import annotations

import re
from html.parser import HTMLParser
from pathlib import Path

from app.schemas.content import QualityCheck, QualityReport
from app.services import generator
from quality.check_rls import check_rls

CI_ONLY_CHECKS = "build, lint, gitleaks, npm audit, smoke: not run here, see quality/generated-repo-ci.yml"
# Token shapes of the providers SpeedHack and generated apps commonly use, plus private keys.
SECRET = re.compile(
    r"AIza[0-9A-Za-z_\-]{35}|sk-[A-Za-z0-9_\-]{20,}|sk_live_[0-9A-Za-z]{20,}|ghp_[0-9A-Za-z]{36}|"
    r"tvly-[0-9A-Za-z]{20,}|fc-[0-9a-f]{32}|AKIA[0-9A-Z]{16}|lin_api_[0-9A-Za-z]{20,}|xox[bp]-[0-9A-Za-z\-]{20,}|"
    r"-----BEGIN [A-Z ]*PRIVATE KEY-----"
)
SMOKE_URL = "http://prototype.speedhack.invalid/"
DANGEROUS_JS = re.compile(r"\beval\s*\(|\bnew\s+Function\s*\(|\bdocument\.write\s*\(")


def _build(html: str) -> QualityCheck | None:
    try:
        HTMLParser().feed(html)
    except Exception as exc:  # noqa: BLE001  (any parser failure is the finding)
        return QualityCheck(name="build", passed=False, details=f"el HTML no se puede leer: {exc}")
    scripts = generator.inline_scripts(html)
    errors = [generator.node_check(js) for js in scripts]
    if any(e is None for e in errors):
        return None
    bad = [e for e in errors if e]
    if bad:
        return QualityCheck(name="build", passed=False, details=f"node --check: {bad[0]}")
    return QualityCheck(name="build", passed=True, details=f"HTML leído y {len(scripts)} script(s) válidos con node --check")


def _lint(html: str) -> QualityCheck:
    rules = (
        ("recursos externos", generator.EXTERNAL_REF),
        ("llamadas de red", generator.NETWORK_API),
        ("almacenamiento del navegador", generator.STORAGE_API),
        ("eval / new Function / document.write", DANGEROUS_JS),
    )
    found = [what for what, rx in rules if rx.search(html)]
    if found:
        return QualityCheck(name="lint", passed=False, details="encontrado: " + ", ".join(found))
    return QualityCheck(name="lint", passed=True, details="sin recursos externos, llamadas de red ni eval")


def _secrets(html: str) -> QualityCheck:
    hits = len(SECRET.findall(html))
    if hits:
        return QualityCheck(name="secrets", passed=False, details=f"{hits} posible(s) clave(s) en el código")
    return QualityCheck(name="secrets", passed=True, details="ninguna clave reconocible en el archivo")


def _smoke(path: Path) -> QualityCheck | None:
    try:
        from playwright.sync_api import Error as PlaywrightError
        from playwright.sync_api import sync_playwright
    except ImportError:
        return None
    errors: list[str] = []
    html = path.read_text(encoding="utf-8")

    def serve(route) -> None:
        # Served exactly as /api/prototypes serves it (CSP sandbox, no network); any other request is refused.
        if route.request.url == SMOKE_URL:
            route.fulfill(status=200, body=html, headers={"Content-Type": "text/html; charset=utf-8",
                                                          "Content-Security-Policy": generator.CSP})
        else:
            route.abort()

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch()
            try:
                page = browser.new_page()
                page.on("pageerror", lambda e: errors.append(str(e)))
                page.on("console", lambda m: errors.append(m.text) if m.type == "error" else None)
                page.route("**/*", serve)
                page.goto(SMOKE_URL)
                page.wait_for_timeout(500)
                text = page.inner_text("body").strip()
            finally:
                browser.close()
    except PlaywrightError:
        return None  # no browser installed here: not run
    if errors:
        return QualityCheck(name="smoke", passed=False, details=f"error al abrir: {errors[0][:200]}")
    if not text:
        return QualityCheck(name="smoke", passed=False, details="la página abre en blanco")
    return QualityCheck(name="smoke", passed=True, details="abre aislada, sin red y sin errores de JavaScript")


def check_app(path: str | Path, *, demo_data: bool = False) -> QualityReport:
    """Real checks on the single page SpeedHack generated; missing tools are reported as not run."""
    path = Path(path)
    html = path.read_text(encoding="utf-8")
    ran = {"build": _build(html), "lint": _lint(html), "secrets": _secrets(html), "smoke": _smoke(path)}
    checks = [c for c in ran.values() if c is not None]
    skipped = [name for name, c in ran.items() if c is None]
    return QualityReport(
        checks=checks,
        passed=bool(checks) and all(c.passed for c in checks),
        details=f"no ejecutado aquí: {', '.join(skipped)}" if skipped else "",
        demo_data=demo_data,
    )


def run(repo_path: str | Path, *, demo_data: bool = False) -> QualityReport:
    rls = check_rls(repo_path)
    checks = [QualityCheck(name="rls", passed=rls.passed, details=rls.details)]
    return QualityReport(
        checks=checks,
        passed=all(c.passed for c in checks),
        details=CI_ONLY_CHECKS,
        demo_data=demo_data,
    )
