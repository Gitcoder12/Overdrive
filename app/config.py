"""
Overdrive configuration.

Loads environment variables with validation.
Supports multiple LLM providers via LLM_PROVIDER.
"""

from __future__ import annotations

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Which provider to use
    llm_provider: str = Field(
        default="anthropic",
        description="anthropic | openai | google | groq | ollama",
    )
    llm_model: str = Field(
        default="",
        description="Model name; empty = provider default",
    )
    max_tokens: int = Field(default=2000, ge=100, le=8000)

    # Provider API keys (only one needed, based on llm_provider)
    anthropic_api_key: str | None = None
    openai_api_key: str | None = None
    google_api_key: str | None = None
    groq_api_key: str | None = None

    # Ollama (local)
    ollama_base_url: str = "http://localhost:11434"

    app_name: str = "Overdrive"
    app_version: str = "0.1.0"
    debug: bool = False


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return cached settings instance."""
    return Settings()
