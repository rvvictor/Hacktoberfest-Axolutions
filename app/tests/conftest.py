"""Every test starts from the no-key demo configuration, whatever the developer's `.env` holds.

`app.config.settings` and the LLM service's Gemini settings read `.env` at import time, so a
filled `.env` (DEMO_MODE=false, real keys, a Gemma model) would make tests call real APIs and
spend credits. This autouse fixture resets them before each test; a test that needs live mode
still sets it explicitly with `monkeypatch`, which runs after this fixture.
"""

import pytest

from app.config import Settings, settings
from app.services import llm

DEMO_DEFAULTS = {"DEMO_MODE": True, "LLM_MODEL": Settings.model_fields["LLM_MODEL"].default}
KEPT = {"DATA_DIR"}  # where the store writes; not a credential


@pytest.fixture(autouse=True)
def no_real_credentials(monkeypatch):
    for name in Settings.model_fields:
        if name in KEPT:
            continue
        monkeypatch.setattr(settings, name, DEMO_DEFAULTS.get(name))
    monkeypatch.setattr(llm.gemini_env, "GEMINI_API_KEY", None)
