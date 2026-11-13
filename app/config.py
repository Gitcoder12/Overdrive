"""
Overdrive configuration.

Loads environment variables with validation.
Supports multiple LLM providers via LLM_PROVIDER.
"""

from __future__ import annotations

import logging
from functools import lru_cache

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger("Overdrive.Config")

class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # --- Core App Settings ---
    app_name: str = "Overdrive"
    app_version: str = "0.1.0"
    debug: bool = False

    # --- LLM Configuration ---
    llm_provider: str = Field(
        default="anthropic",
        description="anthropic | openai | google | groq | deepseek | openrouter | ollama",
    )
    llm_model: str = Field(
        default="",
        description="Model name; empty = provider default",
    )
    max_tokens: int = Field(default=2000, ge=100, le=8000)
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)

    # --- Provider API Keys ---
    anthropic_api_key: str | None = None
    openai_api_key: str | None = None
    google_api_key: str | None = None
    groq_api_key: str | None = None
    deepseek_api_key: str | None = None
    openrouter_api_key: str | None = None

    # --- Local / Self-Hosted ---
    ollama_base_url: str = "http://localhost:11434"

    @model_validator(mode="after")
    def validate_api_keys(self) -> Settings:
        """Ensure the selected provider has an API key before starting."""
        provider = self.llm_provider.lower()

        key_map = {
            "anthropic": self.anthropic_api_key,
            "openai": self.openai_api_key,
            "google": self.google_api_key,
            "groq": self.groq_api_key,
            "deepseek": self.deepseek_api_key,
            "openrouter": self.openrouter_api_key,
        }

        if provider != "ollama" and provider in key_map and not key_map[provider]:
            logger.warning(
                "Missing API key for selected provider: %s. Provider requests will be unavailable.",
                provider.upper(),
            )

        return self


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return cached settings instance."""
    return Settings()
