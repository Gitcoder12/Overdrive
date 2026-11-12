"""
Overdrive — FastAPI entry point.

Endpoints:
    GET  /health    → health check + active provider
    POST /analyze   → analyze a process with any LLM provider
"""

from __future__ import annotations

import json
import logging
from typing import Any, Literal

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.concurrency import run_in_threadpool
from pydantic import BaseModel, Field

from app.config import Settings, get_settings
from app.llm import LLMProvider, get_provider

logger = logging.getLogger(__name__)

app = FastAPI(
    title="Overdrive",
    description="AI-powered field intelligence and optimization engine",
    version="0.1.0",
)

# ---------- Schemas ----------

class AnalyzeRequest(BaseModel):
    """Request payload for /analyze."""
    process: str = Field(..., min_length=10, max_length=5000)
    data: dict[str, Any] | None = None


class Bottleneck(BaseModel):
    """A single ranked bottleneck."""
    rank: int = Field(ge=1)
    name: str
    severity: Literal["high", "medium", "low"]
    root_cause: str
    fix: str
    roi_estimate: str
    confidence: float = Field(ge=0.0, le=1.0)


class AnalyzeResponse(BaseModel):
    """Response payload for /analyze."""
    provider: str
    bottlenecks: list[Bottleneck] = Field(min_length=3, max_length=7)
    summary: str = Field(min_length=1)


# ---------- Prompt ----------

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
      "roi_estimate": "$45K/year",
      "confidence": 0.87
    }
  ],
  "summary": "one paragraph overview"
}

Rules:
- Rank from highest impact to lowest.
- severity must be one of: high, medium, low.
- confidence is a float between 0.0 and 1.0.
- Return 3 to 7 bottlenecks.
"""


# ---------- Endpoints ----------

@app.get("/health")
async def health(settings: Settings = Depends(get_settings)) -> dict[str, str]:
    """Health check + active provider."""
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
    settings: Settings = Depends(get_settings),
) -> AnalyzeResponse:
    """Analyze a process with the configured LLM provider."""

    # 1. Initialize LLM
    try:
        llm: LLMProvider = get_provider(settings)
    except ValueError as exc:
        logger.warning("LLM provider configuration is unavailable: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="The configured LLM provider is unavailable or incorrectly configured.",
        ) from exc

    # 2. Build Prompt (Sanitized)
    # We wrap user data in XML tags to help the LLM separate instructions from data.
    user_message = f"<process_description>\n{req.process}\n</process_description>"
    if req.data:
        user_message += f"\n\n<process_data>\n{json.dumps(req.data, indent=2)}\n</process_data>"

    # 3. Call LLM (Non-blocking)
    try:
        # We run the synchronous LLM call in a separate thread so it doesn't block FastAPI
        text = await run_in_threadpool(llm.complete, SYSTEM_PROMPT, user_message, settings.max_tokens)
    except Exception as exc:
        logger.exception("LLM call failed for provider %s", llm.name)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="The configured LLM provider request failed.",
        ) from exc

    # 4. Parse and validate the provider response.
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
        parsed, _ = json.JSONDecoder().raw_decode(text[start_idx:])
    except json.JSONDecodeError as exc:
        logger.warning("LLM provider %s returned invalid JSON: %s", llm.name, exc)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="The LLM provider returned malformed JSON.",
        ) from exc

    if not isinstance(parsed, dict):
        logger.warning("LLM provider %s returned JSON with an invalid top-level type", llm.name)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="The LLM provider response must be a JSON object.",
        )

    try:
        return AnalyzeResponse.model_validate({**parsed, "provider": llm.name})
    except (TypeError, ValueError) as exc:
        logger.warning("LLM provider %s returned an invalid response schema: %s", llm.name, exc)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="The LLM provider response did not match the required schema.",
        ) from exc
