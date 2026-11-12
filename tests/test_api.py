"""API tests for Overdrive."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def _valid_completion() -> str:
    return """
    {
      "bottlenecks": [
        {
          "rank": 1,
          "name": "Inventory check failures",
          "severity": "high",
          "root_cause": "No real-time sync",
          "fix": "Use event-driven synchronization",
          "roi_estimate": "Requires measurement",
          "confidence": 0.87
        },
        {
          "rank": 2,
          "name": "Inspection queue",
          "severity": "medium",
          "root_cause": "Insufficient inspection capacity",
          "fix": "Balance inspection staffing",
          "roi_estimate": "Requires measurement",
          "confidence": 0.72
        },
        {
          "rank": 3,
          "name": "Dispatch batching",
          "severity": "low",
          "root_cause": "Static dispatch batches",
          "fix": "Evaluate smaller dynamic batches",
          "roi_estimate": "Requires measurement",
          "confidence": 0.61
        }
      ],
      "summary": "Three candidate bottlenecks identified for validation."
    }
    """


def test_health() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["service"] == "overdrive"
    assert "provider" in body


def test_analyze_validation_short_process() -> None:
    response = client.post("/analyze", json={"process": "hi"})
    assert response.status_code == 422


def test_analyze_validation_missing_process() -> None:
    response = client.post("/analyze", json={})
    assert response.status_code == 422


@patch("app.main.get_provider")
def test_analyze_success(mock_get_provider: MagicMock) -> None:
    fake_llm = MagicMock()
    fake_llm.name = "fake:model"
    fake_llm.complete.return_value = _valid_completion()
    mock_get_provider.return_value = fake_llm

    response = client.post(
        "/analyze",
        json={
            "process": "Order fulfillment: order to inventory to pick to ship",
            "data": {"avg_hrs": 4.2},
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["provider"] == "fake:model"
    assert len(body["bottlenecks"]) == 3
    assert body["bottlenecks"][0]["name"] == "Inventory check failures"
    assert body["summary"] == "Three candidate bottlenecks identified for validation."


@pytest.mark.parametrize(
    "provider_output",
    [
        "Sorry, I cannot return structured output.",
        "{not valid json}",
        "[]",
    ],
)
@patch("app.main.get_provider")
def test_analyze_rejects_invalid_provider_output(
    mock_get_provider: MagicMock,
    provider_output: str,
) -> None:
    fake_llm = MagicMock()
    fake_llm.name = "fake:model"
    fake_llm.complete.return_value = provider_output
    mock_get_provider.return_value = fake_llm

    response = client.post(
        "/analyze",
        json={"process": "Order fulfillment: order to inventory to ship"},
    )

    assert response.status_code == 502


@patch("app.main.get_provider")
def test_analyze_rejects_invalid_bottleneck_schema(mock_get_provider: MagicMock) -> None:
    import json

    payload = json.loads(_valid_completion())
    payload["bottlenecks"][0]["severity"] = "urgent"

    fake_llm = MagicMock()
    fake_llm.name = "fake:model"
    fake_llm.complete.return_value = json.dumps(payload)
    mock_get_provider.return_value = fake_llm

    response = client.post(
        "/analyze",
        json={"process": "Order fulfillment: order to inventory to ship"},
    )

    assert response.status_code == 502
