"""
LLM provider abstraction.

Any provider implements .complete(system, user, max_tokens) -> str.
Swap providers via LLM_PROVIDER env var.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from app.config import Settings


class LLMProvider(ABC):
    """Abstract LLM provider."""

    @abstractmethod
    def complete(self, system: str, user: str, max_tokens: int) -> str:
        """Return raw text completion."""
        ...

    @property
    @abstractmethod
    def name(self) -> str:
        """Human-readable provider name."""
        ...


def get_provider(settings: Settings) -> LLMProvider:
    """Factory: return provider based on settings.llm_provider."""
    from app.llm.providers import (
        AnthropicProvider,
        GoogleProvider,
        GroqProvider,
        OllamaProvider,
        OpenAIProvider,
    )

    registry: dict[str, type[LLMProvider]] = {
        "anthropic": AnthropicProvider,
        "openai": OpenAIProvider,
        "google": GoogleProvider,
        "groq": GroqProvider,
        "ollama": OllamaProvider,
    }

    key = settings.llm_provider.lower()
    if key not in registry:
        raise ValueError(
            f"Unknown provider '{key}'. "
            f"Choose from: {', '.join(registry)}"
        )

    return registry[key](settings)
