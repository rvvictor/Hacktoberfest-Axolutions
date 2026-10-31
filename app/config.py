from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    DEMO_MODE: bool = True
    DATA_DIR: Path = Path("data")
    LLM_MODEL: str = "claude-sonnet-5-5"

    ANTHROPIC_API_KEY: str | None = None
    BACKBOARD_API_KEY: str | None = None
    ELEVENLABS_API_KEY: str | None = None
    ELEVENLABS_VOICE_ID: str | None = None
    ELEVENLABS_AGENT_ID: str | None = None
    ELEVENLABS_DAILY_CHARS: int = 5000  # paid TTS characters per UTC day, all visitors; placeholder, no budget is set in the repo yet
    TAVILY_API_KEY: str | None = None
    FIRECRAWL_API_KEY: str | None = None
    MIRO_ACCESS_TOKEN: str | None = None
    LINEAR_API_KEY: str | None = None
    LINEAR_TEAM_ID: str | None = None
    LOVABLE_PREBUILT_URL: str | None = None
    N8N_WEBHOOK_URL: str | None = None
    N8N_WEBHOOK_SECRET: str | None = None

    # Accounts (spec 001). AUTH_REQUIRED stays false until accounts persist on the deployment (ADR 0002).
    GOOGLE_CLIENT_ID: str | None = None
    GOOGLE_CLIENT_SECRET: str | None = None
    OWNER_EMAIL: str | None = None
    AUTH_REQUIRED: bool = False
    PUBLIC_URL: str | None = None  # e.g. https://speedhack.onrender.com; the OAuth redirect is built from it behind a proxy
    RUNS_PER_USER_PER_DAY: int = 1


settings = Settings()
