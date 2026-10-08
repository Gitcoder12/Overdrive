"""
Overdrive — FastAPI entry point.

Endpoints:
    GET  /health    → health check
    POST /analyze   → analyze a process with Claude
"""

from __future__ import annotations

import json
import logging
import re
from typing import Any

from anthropic import Anthropic
from fastapi import Depends, FastAPI, HTTPException, status
from pydantic import BaseModel, Field

from app.config import Settings, get_settings

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

    bottlenecks: list[Bottleneck]
    summary: str


# ---------- Claude prompt ----------

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


def get_claude(settings: Settings = Depends(get_settings)) -> Anthropic:
    """Dependency: return Anthropic client."""
    return Anthropic(api_key=settings.anthropic_api_key)


# ---------- Endpoints ----------

@app.get("/health")
def health() -> dict[str, str]:
    """Basic health check."""
    return {"status": "ok", "service": "overdrive"}


@app.post(
    "/analyze",
    response_model=AnalyzeResponse,
    status_code=status.HTTP_200_OK,
)
def analyze(
    req: AnalyzeRequest,
    settings: Settings = Depends(get_settings),
    client: Anthropic = Depends(get_claude),
) -> AnalyzeResponse:
    """Analyze a process and return ranked bottlenecks."""

    user_message = f"Process:\n{req.process}"
    if req.data:
        user_message += f"\n\nData:\n{json.dumps(req.data, indent=2)}"

    try:
        response = client.messages.create(
            model=settings.anthropic_model,
            max_tokens=settings.max_tokens,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_message}],
        )
    except Exception as exc:
        logger.exception("Claude API call failed")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Claude API error: {exc}",
        ) from exc

    text = response.content[0].text.strip()

    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not extract JSON from Claude response",
        )

    try:
        parsed = json.loads(match.group())
    except json.JSONDecodeError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Invalid JSON from Claude: {exc}",
        ) from exc

    bottlenecks = [Bottleneck(**b) for b in parsed.get("bottlenecks", [])]

    return AnalyzeResponse(
        bottlenecks=bottlenecks,
        summary=parsed.get("summary", ""),
    )
