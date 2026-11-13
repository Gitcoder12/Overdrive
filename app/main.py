"""FastAPI entry point for Overdrive's validated process-analysis MVP."""

from __future__ import annotations

import json
import logging
from typing import Any, Literal

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.concurrency import run_in_threadpool
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.config import Settings, get_settings
from app.llm import LLMProvider, get_provider

logger = logging.getLogger(__name__)

app = FastAPI(
    title="Overdrive",
    description="AI-powered field intelligence and optimization engine",
    version="0.1.0",
)


class AnalyzeRequest(BaseModel):
    """Request payload for /analyze."""

    model_config = ConfigDict(extra="forbid")

    process: str = Field(min_length=10, max_length=5000)
    data: dict[str, Any] | None = None

    @field_validator("process")
    @classmethod
    def process_must_contain_text(cls, value: str) -> str:
        normalized = value.strip()
        if len(normalized) < 10:
            raise ValueError("process must contain at least 10 non-whitespace characters")
        return normalized


class Bottleneck(BaseModel):
    """A single ranked bottleneck returned by the model."""

    model_config = ConfigDict(extra="forbid")

    rank: int = Field(ge=1, strict=True)
    name: str = Field(min_length=1, max_length=160)
    severity: Literal["high", "medium", "low"]
    root_cause: str = Field(min_length=1, max_length=1000)
    fix: str = Field(min_length=1, max_length=1000)
    roi_estimate: str = Field(min_length=1, max_length=160)
    confidence: float = Field(ge=0.0, le=1.0, strict=True)

    @field_validator("name", "root_cause", "fix", "roi_estimate")
    @classmethod
    def required_text_must_not_be_blank(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("text fields must not be blank")
        return normalized


class AnalyzeResponse(BaseModel):
    """Validated response payload for /analyze."""

    model_config = ConfigDict(extra="forbid")

    provider: str = Field(min_length=1)
    bottlenecks: list[Bottleneck] = Field(min_length=3, max_length=7)
    summary: str = Field(min_length=1, max_length=2000)

    @field_validator("summary")
    @classmethod
    def summary_must_not_be_blank(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("summary must not be blank")
        return normalized

    @model_validator(mode="after")
    def validate_bottleneck_ranks(self) -> AnalyzeResponse:
        ranks = [item.rank for item in self.bottlenecks]
        expected = list(range(1, len(self.bottlenecks) + 1))
        if ranks != expected:
            raise ValueError("bottleneck ranks must be unique, ascending, and contiguous from 1")
        return self


SYSTEM_PROMPT = """You are a senior process analyst.

Given a process description and optional data, identify the top bottlenecks,
their root causes, and estimated ROI for each fix.

Return ONLY valid JSON in this exact format — no prose, no markdown fences:

{
  "bottlenecks": [
    {
      "rank": 1,
      "name": "short name",
      "severity": "high",
      "root_cause": "one sentence",
      "fix": "one sentence",
      "roi_estimate": "Requires measurement",
      "confidence": 0.87
    }
  ],
  "summary": "one paragraph overview"
}

Rules:
- Rank from highest impact to lowest, starting at 1 with no gaps.
- severity must be one of: high, medium, low.
- confidence is a numeric float between 0.0 and 1.0.
- Return 3 to 7 bottlenecks.
- Never invent measured ROI; say "Requires measurement" when evidence is unavailable.
"""


@app.get("/health")
async def health(settings: Settings = Depends(get_settings)) -> dict[str, str]:  # noqa: B008
    """Health check and active provider."""
    return {
        "status": "ok",
        "service": "overdrive",
        "provider": settings.llm_provider,
    }


@app.post(
    "/analyze",
    response_model=AnalyzeResponse,
    status_code=status.HTTP_200_OK,
)
async def analyze(
    req: AnalyzeRequest,
    settings: Settings = Depends(get_settings),  # noqa: B008
) -> AnalyzeResponse:
    """Analyze a process with the configured LLM provider."""
    try:
        llm: LLMProvider = get_provider(settings)
    except (ValueError, RuntimeError) as exc:
        logger.warning("LLM provider configuration is unavailable: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="The configured LLM provider is unavailable or incorrectly configured.",
        ) from exc

    user_message = f"<process_description>\n{req.process}\n</process_description>"
    if req.data:
        user_message += (
            f"\n\n<process_data>\n{json.dumps(req.data, ensure_ascii=False)}"
            "\n</process_data>"
        )

    try:
        text = await run_in_threadpool(
            llm.complete,
            SYSTEM_PROMPT,
            user_message,
            settings.max_tokens,
        )
    except Exception as exc:
        logger.exception("LLM call failed for provider %s", llm.name)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="The configured LLM provider request failed.",
        ) from exc

    if not isinstance(text, str):
        logger.error("LLM provider %s returned a non-text response", llm.name)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="The LLM provider returned a non-text response.",
        )

    start_idx = text.find("{")
    if start_idx == -1:
        logger.error("LLM provider %s returned no JSON object", llm.name)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="The LLM provider returned no JSON object.",
        )

    try:
        parsed, end_idx = json.JSONDecoder().raw_decode(text[start_idx:])
    except json.JSONDecodeError as exc:
        logger.warning("LLM provider %s returned malformed JSON", llm.name)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="The LLM provider returned malformed JSON.",
        ) from exc

    if text[start_idx + end_idx :].strip():
        logger.warning("LLM provider %s returned trailing non-JSON content", llm.name)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="The LLM provider response must contain only one JSON object.",
        )

    if not isinstance(parsed, dict):
        logger.warning("LLM provider %s returned a non-object JSON value", llm.name)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="The LLM provider response must be a JSON object.",
        )

    try:
        return AnalyzeResponse.model_validate({**parsed, "provider": llm.name})
    except (TypeError, ValueError) as exc:
        logger.warning("LLM provider %s returned an invalid response schema", llm.name)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="The LLM provider response did not match the required schema.",
        ) from exc
