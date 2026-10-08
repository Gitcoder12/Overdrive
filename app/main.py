"""
Overdrive — FastAPI entry point.

Endpoints:
    GET  /health    → health check + active provider
    POST /analyze   → analyze a process with any LLM provider
"""

from __future__ import annotations

import json
import logging
import re
from typing import Any

from fastapi import Depends, FastAPI, HTTPException, status
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

    rank: int
    name: str
    severity: str
    root_cause: str
    fix: str
    roi_estimate: str
    confidence: float = Field(ge=0.0, le=1.0)


class AnalyzeResponse(BaseModel):
    """Response payload for /analyze."""

    provider: str
    bottlenecks: list[Bottleneck]
    summary: str


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


def get_llm(settings: Settings = Depends(get_settings)) -> LLMProvider:
    """Dependency: return active LLM provider."""
    try:
        return get_provider(settings)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc


# ---------- Endpoints ----------

@app.get("/health")
def health(settings: Settings = Depends(get_settings)) -> dict[str, str]:
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
def analyze(
    req: AnalyzeRequest,
    settings: Settings = Depends(get_settings),
    llm: LLMProvider = Depends(get_llm),
) -> AnalyzeResponse:
    """Analyze a process with the configured LLM provider."""

    user_message = f"Process:\n{req.process}"
    if req.data:
        user_message += f"\n\nData:\n{json.dumps(req.data, indent=2)}"

    try:
        text = llm.complete(SYSTEM_PROMPT, user_message, settings.max_tokens)
    except Exception as exc:
        logger.exception("LLM call failed")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"LLM error ({llm.name}): {exc}",
        ) from exc

    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Could not extract JSON from {llm.name} response",
        )

    try:
        parsed = json.loads(match.group())
    except json.JSONDecodeError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Invalid JSON from {llm.name}: {exc}",
        ) from exc

    bottlenecks = [Bottleneck(**b) for b in parsed.get("bottlenecks", [])]

    return AnalyzeResponse(
        provider=llm.name,
        bottlenecks=bottlenecks,
        summary=parsed.get("summary", ""),
    )
