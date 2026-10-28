from pathlib import Path
from urllib.parse import unquote

from app.config import settings
from app.schemas.content import BacklogItem, Prototype, Spec
from app.services import generator
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
