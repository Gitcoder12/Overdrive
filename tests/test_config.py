"""Config tests for Overdrive."""

from __future__ import annotations

from app.config import Settings


def test_default_provider() -> None:
    """Default provider is anthropic."""
    settings = Settings()
    assert settings.llm_provider == "anthropic"


def test_default_max_tokens() -> None:
    """Default max_tokens is 2000."""
    settings = Settings()
    assert settings.max_tokens == 2000


def test_ollama_default_url() -> None:
    """Ollama default URL is correct."""
    settings = Settings()
    assert settings.ollama_base_url == "http://localhost:11434"


def test_api_keys_optional() -> None:
    """All provider API keys can be None."""
    settings = Settings()
    assert settings.anthropic_api_key is None
    assert settings.openai_api_key is None
    assert settings.google_api_key is None
    assert settings.groq_api_key is None
