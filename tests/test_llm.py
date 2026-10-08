"""LLM provider tests for Overdrive."""

from __future__ import annotations

import pytest

from app.config import Settings
from app.llm.base import get_provider


def test_get_provider_unknown() -> None:
    """Unknown provider raises ValueError."""
    settings = Settings()
    settings.llm_provider = "doesnotexist"
    with pytest.raises(ValueError, match="Unknown provider"):
        get_provider(settings)


def test_get_provider_anthropic_no_key() -> None:
    """Anthropic provider without key raises ValueError."""
    settings = Settings()
    settings.llm_provider = "anthropic"
    settings.anthropic_api_key = None
    with pytest.raises(ValueError, match="ANTHROPIC_API_KEY"):
        get_provider(settings)


def test_get_provider_openai_no_key() -> None:
    """OpenAI provider without key raises ValueError."""
    settings = Settings()
    settings.llm_provider = "openai"
    settings.openai_api_key = None
    with pytest.raises(ValueError, match="OPENAI_API_KEY"):
        get_provider(settings)


def test_get_provider_google_no_key() -> None:
    """Google provider without key raises ValueError."""
    settings = Settings()
    settings.llm_provider = "google"
    settings.google_api_key = None
    with pytest.raises(ValueError, match="GOOGLE_API_KEY"):
        get_provider(settings)


def test_get_provider_groq_no_key() -> None:
    """Groq provider without key raises ValueError."""
    settings = Settings()
    settings.llm_provider = "groq"
    settings.groq_api_key = None
    with pytest.raises(ValueError, match="GROQ_API_KEY"):
        get_provider(settings)
