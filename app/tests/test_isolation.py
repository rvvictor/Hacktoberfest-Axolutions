from app.config import Settings, settings
from app.services import llm


def test_tests_never_see_real_credentials():
    # Compare names and booleans only: a failure must never print a credential.
    demo_mode_on = settings.DEMO_MODE is True
    default_model = settings.LLM_MODEL == Settings.model_fields["LLM_MODEL"].default
    gemini_key_set = llm.gemini_env.GEMINI_API_KEY is not None
    filled = [
        name
        for name in Settings.model_fields
        if name not in {"DEMO_MODE", "DATA_DIR", "LLM_MODEL"} and getattr(settings, name) is not None
    ]
    assert demo_mode_on
    assert default_model
    assert not gemini_key_set
    assert filled == []


def test_a_test_can_still_opt_into_live_mode(monkeypatch):
    monkeypatch.setattr(settings, "DEMO_MODE", False)
    assert settings.DEMO_MODE is False
