"""API tests for Overdrive."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health() -> None:
    """Health endpoint returns ok + provider."""
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["service"] == "overdrive"
    assert "provider" in body


def test_analyze_validation_short_process() -> None:
    """Process under 10 chars fails validation."""
    response = client.post("/analyze", json={"process": "hi"})
    assert response.status_code == 422


def test_analyze_validation_missing_process() -> None:
    """Missing process field fails validation."""
    response = client.post("/analyze", json={})
    assert response.status_code == 422


@patch("app.main.get_provider")
def test_analyze_success(mock_get_provider: MagicMock) -> None:
    """Analyze returns parsed bottlenecks from LLM response."""
    fake_llm = MagicMock()
    fake_llm.name = "fake:model"
    fake_llm.complete.return_value = """
    {
      "bottlenecks": [
        {
          "rank": 1,
          "name": "Inventory check failures",
          "severity": "high",
          "root_cause": "No real-time sync",
          "fix": "Event-driven sync",
          "roi_estimate": "$45K/year",
          "confidence": 0.87
        }
      ],
      "summary": "One high-impact bottleneck identified."
    }
    """
    mock_get_provider.return_value = fake_llm

    payload = {
        "process": "Order fulfillment: order → inventory → pick → ship",
        "data": {"avg_hrs": 4.2},
    }
    response = client.post("/analyze", json=payload)
    assert response.status_code == 200
    body = response.json()
    assert body["provider"] == "fake:model"
    assert len(body["bottlenecks"]) == 1
    assert body["bottlenecks"][0]["name"] == "Inventory check failures"
    assert body["summary"] == "One high-impact bottleneck identified."


@patch("app.main.get_provider")
def test_analyze_invalid_json_from_llm(mock_get_provider: MagicMock) -> None:
    """Non-JSON response returns 500."""
    fake_llm = MagicMock()
    fake_llm.name = "fake:model"
    fake_llm.complete.return_value = "Sorry, I can't help with that."
    mock_get_provider.return_value = fake_llm

    payload = {"process": "Order fulfillment: order → inventory → ship"}
    response = client.post("/analyze", json=payload)
    assert response.status_code == 500
