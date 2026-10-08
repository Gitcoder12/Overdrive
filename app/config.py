"""
Overdrive configuration.

Loads environment variables with validation.
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

    anthropic_api_key: str = Field(..., description="Anthropic API key")
    anthropic_model: str = Field(
        default="claude-sonnet-4-20250514",
        description="Claude model to use",
    )
    max_tokens: int = Field(default=2000, ge=100, le=8000)
    app_name: str = Field(default="Overdrive")
    app_version: str = Field(default="0.1.0")
    debug: bool = Field(default=False)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return cached settings instance."""
    return Settings()
