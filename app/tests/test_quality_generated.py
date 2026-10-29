"""Quality gate on the app SpeedHack generated, and the sandboxed route that serves it."""

import shutil

import pytest
from fastapi.testclient import TestClient

from app.config import settings
from app.main import app
from app.schemas import Mode
from app.services import generator, quality, store

GOOD = "<!DOCTYPE html><html><body><h1>Gastos</h1><script>document.body.dataset.ok = '1';</script></body></html>"


def _write(tmp_path, html):
    path = tmp_path / "index.html"
    path.write_text(html, encoding="utf-8")
    return path


def _by_name(report):
    return {c.name: c for c in report.checks}


def test_clean_app_passes_every_check_that_ran(tmp_path):
    report = quality.check_app(_write(tmp_path, GOOD))
    checks = _by_name(report)
    assert {"lint", "secrets"} <= checks.keys()
    assert all(c.passed for c in report.checks) and report.passed
    # whatever could not run here is named as not run, never reported as passed
    for name in {"build", "smoke"} - checks.keys():
        assert name in report.details


def test_findings_fail_their_checks(tmp_path):
    key = "AIza" + "x" * 35
    html = f"<!DOCTYPE html><html><body><script>eval('1'); const k = '{key}';</script></body></html>"
    checks = _by_name(quality.check_app(_write(tmp_path, html)))
    assert checks["lint"].passed is False and "eval" in checks["lint"].details
    assert checks["secrets"].passed is False and key not in checks["secrets"].details


@pytest.mark.skipif(shutil.which("node") is None, reason="node not installed")
def test_build_runs_node_check(tmp_path):
    bad = _write(tmp_path, "<!DOCTYPE html><html><body><script>let = ;</script></body></html>")
    assert _by_name(quality.check_app(bad))["build"].passed is False
    assert "node --check" in _by_name(quality.check_app(_write(tmp_path, GOOD)))["build"].details


def test_missing_tools_are_not_run_not_passed(tmp_path, monkeypatch):
    monkeypatch.setattr(generator.shutil, "which", lambda _name: None)
    monkeypatch.setattr(quality, "_smoke", lambda _path: None)
    report = quality.check_app(_write(tmp_path, GOOD))
    assert "build" not in _by_name(report) and "smoke" not in _by_name(report)
    assert report.details == "no ejecutado aquí: build, smoke"


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "DATA_DIR", tmp_path)
    return TestClient(app)


def test_route_serves_the_app_sandboxed(client):
    _, run = store.create_run(Mode.dev, "SaaS de gastos", [], demo_data=False)
    run_id = run.run_id
    path = generator.prototype_path(run_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(GOOD, encoding="utf-8")
    r = client.get(f"/api/prototypes/{run_id}/")
    assert r.status_code == 200 and "<h1>Gastos</h1>" in r.text
    csp = r.headers["content-security-policy"]
    assert "default-src 'none'" in csp and "sandbox allow-scripts" in csp and "allow-same-origin" not in csp
    assert "frame-ancestors 'self'" in csp and r.headers["x-content-type-options"] == "nosniff"


@pytest.mark.parametrize("run_id", ["run_ffffffff", "..%2F..%2Fetc", "run_0000ABCD"])
def test_route_404s_unknown_or_malformed_runs(client, run_id):
    assert client.get(f"/api/prototypes/{run_id}/").status_code == 404


def test_smoke_runs_the_page_under_the_served_sandbox(tmp_path):
    # localStorage works from a file but throws inside the CSP sandbox the route serves: smoke must see that.
    html = "<!DOCTYPE html><html><body><p>x</p><script>window['local' + 'Storage'].setItem('a', '1');</script></body></html>"
    smoke = quality._smoke(_write(tmp_path, html))
    if smoke is None:
        pytest.skip("no browser here")
    assert smoke.passed is False and "error" in smoke.details


def test_storage_apis_are_rejected_and_flagged(tmp_path):
    html = "<!DOCTYPE html><html><body><script>localStorage.setItem('a', '1');</script></body></html>"
    with pytest.raises(ValueError, match="localStorage"):
        generator.validate_app(html)
    assert _by_name(quality.check_app(_write(tmp_path, html)))["lint"].passed is False
