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
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
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
        logger.exception("LLM call failed")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"LLM error ({llm.name}): {exc}",
        ) from exc

    # 4. Robust JSON Extraction
    # Instead of regex, we use the JSON Decoder to find the first valid JSON object.
    try:
        # Find the first '{' and try to decode from there
        start_idx = text.find('{')
        if start_idx == -1:
            raise ValueError("No JSON object found in response")
            
        parsed, _ = json.JSONDecoder().raw_decode(text[start_idx:])
        
    except json.JSONDecodeError as exc:
        logger.error(f"Invalid JSON from {llm.name}: {text[:200]}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Invalid JSON from {llm.name}: {exc}",
        ) from exc

    # 5. Parse and Validate
    try:
        raw_bottlenecks = parsed.get("bottlenecks", [])
        bottlenecks = [Bottleneck(**b) for b in raw_bottlenecks]
        summary = parsed.get("summary", "")
    except Exception as exc:
        logger.error(f"Pydantic validation failed for LLM output: {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="LLM returned JSON that did not match the required schema.",
        ) from exc

    return AnalyzeResponse(
        provider=llm.name,
        bottlenecks=bottlenecks,
        summary=summary,
    )
