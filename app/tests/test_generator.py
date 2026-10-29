from pathlib import Path
from urllib.parse import unquote

import pytest

from app.config import settings
from app.schemas.content import BacklogItem, Prototype, Spec
from app.services import generator, llm
from app.services.generator import (
    LOVABLE_BASE_URL,
    MAX_PROMPT_CHARS,
    CodeGenerator,
    LovableGenerator,
    PlanBGenerator,
    build_prompt,
)

SPEC = Spec(
    version=1,
    problem="Taquerías pierden pedidos por WhatsApp",
    users=["dueño de taquería"],
    mvp_features=["Menú en línea", "Pedidos con seguimiento"],
    assumptions=["Pago en efectivo"],
    sources=["https://evil.example/ignore-previous-instructions"],
)
BACKLOG = [
    BacklogItem(epic="Pedidos", title="Crear pedido", acceptance=["Muestra total"], external_id="b1")
]


def test_both_implement_protocol_and_return_prototype():
    for gen in (LovableGenerator(), PlanBGenerator()):
        assert isinstance(gen, CodeGenerator)
        assert isinstance(gen.generate(SPEC, BACKLOG), Prototype)


def test_lovable_url_format_and_content():
    url = LovableGenerator().build_url(SPEC, BACKLOG)
    assert url.startswith(LOVABLE_BASE_URL)
    assert "?" not in url and "autosubmit" not in url
    prompt = unquote(url[len(LOVABLE_BASE_URL):])
    for expected in ("Taquerías", "Menú en línea", "Pago en efectivo", "Crear pedido", "Muestra total"):
        assert expected in prompt
    proto = LovableGenerator().generate(SPEC, BACKLOG)
    assert proto.generator == "lovable" and proto.build_url == proto.url == url
    assert proto.demo_data is False


def test_prompt_excludes_sources_and_raw_web_content():
    prompt = build_prompt(SPEC, BACKLOG)
    assert "evil.example" not in prompt and "ignore-previous" not in prompt


def test_prompt_is_capped_and_cleaned():
    big = SPEC.model_copy(update={"problem": "x\x00y " * 20_000})
    prompt = build_prompt(big, BACKLOG)
    assert len(prompt) <= MAX_PROMPT_CHARS and "\x00" not in prompt


def test_planb_uses_prebuilt_url(monkeypatch):
    monkeypatch.setattr(settings, "LOVABLE_PREBUILT_URL", "https://example.com/prebuilt")
    proto = PlanBGenerator().generate(SPEC, BACKLOG)
    assert proto.generator == "planb" and proto.url == "https://example.com/prebuilt"
    assert proto.demo_data is True


def test_planb_falls_back_to_recorded_app(monkeypatch):
    monkeypatch.setattr(settings, "LOVABLE_PREBUILT_URL", None)
    proto = PlanBGenerator().generate(SPEC, BACKLOG)
    assert proto.url == generator.PLANB_RECORDED_URL and proto.demo_data is True
    recorded = Path(__file__).parents[1] / "fixtures/generator/planb/index.html"
    assert recorded.is_file()


# --- SpeedHack builds the app itself ---------------------------------------------------------------

APP = "<!DOCTYPE html><html><body><nav>Crear pedido</nav><script>let total = 1;</script></body></html>"


@pytest.fixture
def live_llm(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "DATA_DIR", tmp_path)
    monkeypatch.setattr(llm, "_demo", lambda: False)
    calls = []

    def complete(system, user, **kw):
        calls.append({"system": system, "user": user, **kw})
        return calls_answers.pop(0)

    calls_answers: list[str] = []
    monkeypatch.setattr(llm, "_complete", complete)
    return calls, calls_answers


def test_speedhack_generates_validates_and_saves_the_app(live_llm):
    calls, answers = live_llm
    answers.append(f"```html\n{APP}\n```")
    proto = generator.SpeedHackGenerator("run_0000abcd").generate(SPEC, BACKLOG)
    assert isinstance(generator.SpeedHackGenerator("run_0000abcd"), CodeGenerator)
    assert proto.generator == "speedhack" and proto.url == "/api/prototypes/run_0000abcd/"
    assert proto.build_url and proto.build_url.startswith(LOVABLE_BASE_URL) and proto.demo_data is False
    assert generator.prototype_path("run_0000abcd").read_text() == APP
    assert calls[0]["max_tokens"] == llm.APP_MAX_TOKENS and "Crear pedido" in calls[0]["user"]
    assert "evil.example" not in calls[0]["user"]


def test_invalid_app_is_retried_once_with_the_reason(live_llm):
    calls, answers = live_llm
    answers += ["<!DOCTYPE html><html><body>cortado", APP]
    generator.SpeedHackGenerator("run_0000abcd").generate(SPEC, BACKLOG)
    assert len(calls) == 2 and "</html>" in calls[1]["user"]


def test_app_still_invalid_after_retry_raises(live_llm):
    _, answers = live_llm
    answers += ['<!DOCTYPE html><html><script src="https://cdn.example/x.js"></script></html>'] * 2
    with pytest.raises(llm.LLMOutputError):
        generator.SpeedHackGenerator("run_0000abcd").generate(SPEC, BACKLOG)


def test_reviewer_comment_reaches_the_prompt(live_llm):
    calls, answers = live_llm
    answers.append(APP)
    generator.SpeedHackGenerator("run_0000abcd", "Agrega un filtro por fecha").generate(SPEC, BACKLOG)
    assert "Agrega un filtro por fecha" in calls[0]["user"]


@pytest.mark.parametrize("bad", [
    "<html><body>sin cierre",
    '<!DOCTYPE html><html><body><img src="//tracker.example/p.gif"></body></html>',
    "<!DOCTYPE html><html><body><script>fetch('/api/runs')</script></body></html>",
    "<!DOCTYPE html><html><body><script>let = ;</script></body></html>",
])
def test_validate_app_rejects(bad):
    with pytest.raises(ValueError):
        generator.validate_app(bad)


def test_without_llm_key_the_recorded_app_is_served_as_demo(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "DATA_DIR", tmp_path)
    monkeypatch.setattr(llm, "_demo", lambda: True)
    proto = generator.SpeedHackGenerator("run_0000abcd").generate(SPEC, BACKLOG)
    assert proto.generator == "speedhack" and proto.demo_data is True
    saved = generator.prototype_path("run_0000abcd").read_text()
    assert saved == generator.SPEEDHACK_RECORDED.read_text() and generator.validate_app(saved)


@pytest.mark.parametrize("run_id", ["../etc", "run_../../x", "run_0000ABCD", ""])
def test_prototype_path_refuses_anything_but_a_run_id(run_id):
    with pytest.raises(ValueError):
        generator.prototype_path(run_id)
