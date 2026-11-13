"""API tests for Overdrive's provider boundary and output schema."""

from __future__ import annotations

import json
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


def _post_with_completion(completion: object) -> object:
    fake_llm = MagicMock()
    fake_llm.name = "fake:model"
    fake_llm.complete.return_value = completion
    with patch("app.main.get_provider", return_value=fake_llm):
        return client.post(
            "/analyze",
            json={"process": "Order fulfillment: order to inventory to ship"},
        )


def test_health() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["service"] == "overdrive"
    assert "provider" in body


def test_analyze_validation_short_process() -> None:
    assert client.post("/analyze", json={"process": "hi"}).status_code == 422


def test_analyze_validation_missing_process() -> None:
    assert client.post("/analyze", json={}).status_code == 422


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
        _valid_completion() + " trailing text",
        123,
        {"bottlenecks": "not a list"},
    ],
)
def test_analyze_rejects_invalid_provider_output(provider_output: object) -> None:
    response = _post_with_completion(provider_output)
    assert response.status_code == 502
    assert "Internal server error" not in response.text


@pytest.mark.parametrize(
    "mutation",
    [
        "duplicate_rank",
        "descending_ranks",
        "too_few",
        "empty_summary",
        "empty_name",
        "invalid_severity",
        "negative_rank",
        "extra_field",
    ],
)
def test_analyze_rejects_invalid_response_schema(mutation: str) -> None:
    payload = json.loads(_valid_completion())
    if mutation == "duplicate_rank":
        payload["bottlenecks"][1]["rank"] = 1
    elif mutation == "descending_ranks":
        payload["bottlenecks"][0]["rank"] = 3
        payload["bottlenecks"][2]["rank"] = 1
    elif mutation == "too_few":
        payload["bottlenecks"] = payload["bottlenecks"][:2]
    elif mutation == "empty_summary":
        payload["summary"] = " "
    elif mutation == "empty_name":
        payload["bottlenecks"][0]["name"] = ""
    elif mutation == "invalid_severity":
        payload["bottlenecks"][0]["severity"] = "urgent"
    elif mutation == "negative_rank":
        payload["bottlenecks"][0]["rank"] = 0
    elif mutation == "extra_field":
        payload["bottlenecks"][0]["unexpected"] = "not allowed"

    response = _post_with_completion(json.dumps(payload))
    assert response.status_code == 502


@patch("app.main.get_provider")
def test_analyze_hides_provider_exception_details(mock_get_provider: MagicMock) -> None:
    fake_llm = MagicMock()
    fake_llm.name = "fake:model"
    fake_llm.complete.side_effect = RuntimeError("secret provider credential leaked")
    mock_get_provider.return_value = fake_llm

    response = client.post(
        "/analyze",
        json={"process": "Order fulfillment: order to inventory to ship"},
    )

    assert response.status_code == 502
    assert "secret provider credential" not in response.text


@patch("app.main.get_provider", side_effect=ValueError("private configuration detail"))
def test_analyze_returns_generic_provider_configuration_error(
    mock_get_provider: MagicMock,
) -> None:
    response = client.post(
        "/analyze",
        json={"process": "Order fulfillment: order to inventory to ship"},
    )

    assert response.status_code == 503
    assert "private configuration detail" not in response.text
