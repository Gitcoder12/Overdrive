"""
Concrete LLM provider implementations.

Each provider wraps a different SDK but exposes the same .complete() API.
"""

from __future__ import annotations

from app.config import Settings
from app.llm.base import LLMProvider


class AnthropicProvider(LLMProvider):
    """Anthropic Claude."""

    def __init__(self, settings: Settings) -> None:
        from anthropic import Anthropic

        if not settings.anthropic_api_key:
            raise ValueError("ANTHROPIC_API_KEY required")
        self._client = Anthropic(api_key=settings.anthropic_api_key)
        self._model = settings.llm_model or "claude-sonnet-4-20250514"

    @property
    def name(self) -> str:
        return f"anthropic:{self._model}"

    def complete(self, system: str, user: str, max_tokens: int) -> str:
        response = self._client.messages.create(
            model=self._model,
            max_tokens=max_tokens,
            system=system,
            messages=[{"role": "user", "content": user}],
        )
        return response.content[0].text


class OpenAIProvider(LLMProvider):
    """OpenAI GPT."""

    def __init__(self, settings: Settings) -> None:
        from openai import OpenAI

        if not settings.openai_api_key:
            raise ValueError("OPENAI_API_KEY required")
        self._client = OpenAI(api_key=settings.openai_api_key)
        self._model = settings.llm_model or "gpt-4o-mini"

    @property
    def name(self) -> str:
        return f"openai:{self._model}"

    def complete(self, system: str, user: str, max_tokens: int) -> str:
        response = self._client.chat.completions.create(
            model=self._model,
            max_tokens=max_tokens,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        )
        return response.choices[0].message.content or ""


class GoogleProvider(LLMProvider):
    """Google Gemini."""

    def __init__(self, settings: Settings) -> None:
        import google.generativeai as genai

        if not settings.google_api_key:
            raise ValueError("GOOGLE_API_KEY required")
        genai.configure(api_key=settings.google_api_key)
        self._genai = genai
        self._model_name = settings.llm_model or "gemini-1.5-flash"

    @property
    def name(self) -> str:
        return f"google:{self._model_name}"

    def complete(self, system: str, user: str, max_tokens: int) -> str:
        model = self._genai.GenerativeModel(
            self._model_name,
            system_instruction=system,
        )
        response = model.generate_content(
            user,
            generation_config={"max_output_tokens": max_tokens},
        )
        return response.text


class GroqProvider(LLMProvider):
    """Groq (fast inference: Llama, Mixtral, Gemma)."""

    def __init__(self, settings: Settings) -> None:
        from groq import Groq

        if not settings.groq_api_key:
            raise ValueError("GROQ_API_KEY required")
        self._client = Groq(api_key=settings.groq_api_key)
        self._model = settings.llm_model or "llama-3.3-70b-versatile"

    @property
    def name(self) -> str:
        return f"groq:{self._model}"

    def complete(self, system: str, user: str, max_tokens: int) -> str:
        response = self._client.chat.completions.create(
            model=self._model,
            max_tokens=max_tokens,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        )
        return response.choices[0].message.content or ""


class OllamaProvider(LLMProvider):
    """Local Ollama (no API key, runs on your machine)."""

    def __init__(self, settings: Settings) -> None:
        import httpx

        self._base_url = settings.ollama_base_url.rstrip("/")
        self._model = settings.llm_model or "llama3.1"
        self._client = httpx.Client(timeout=120.0)

    @property
    def name(self) -> str:
        return f"ollama:{self._model}"

    def complete(self, system: str, user: str, max_tokens: int) -> str:
        response = self._client.post(
            f"{self._base_url}/api/chat",
            json={
                "model": self._model,
                "stream": False,
                "options": {"num_predict": max_tokens},
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
            },
        )
        response.raise_for_status()
        return response.json()["message"]["content"]
