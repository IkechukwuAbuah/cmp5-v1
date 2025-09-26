"""Contract tests for GET /health endpoint."""

import pytest
from fastapi.testclient import TestClient
import time


def test_health_endpoint_returns_200_status(client: TestClient):
    """Test that health endpoint returns 200 OK."""
    response = client.get("/api/v1/health")

    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "version" in data
    assert "timestamp" in data
    assert "services" in data


def test_health_response_schema(client: TestClient):
    """Test that health response matches the expected schema."""
    response = client.get("/api/v1/health")

    data = response.json()

    # Check required fields
    assert "status" in data
    assert "version" in data
    assert "timestamp" in data
    assert "services" in data

    # Check data types
    assert isinstance(data["status"], str)
    assert isinstance(data["version"], str)
    assert isinstance(data["timestamp"], str)  # ISO format string
    assert isinstance(data["services"], dict)

    # Check status values
    assert data["status"] in ["healthy", "degraded", "unhealthy"]


def test_health_endpoint_response_time(client: TestClient):
    """Test that health endpoint responds within acceptable time."""
    start_time = time.time()
    response = client.get("/api/v1/health")
    end_time = time.time()

    response_time_ms = (end_time - start_time) * 1000

    assert response.status_code == 200
    assert response_time_ms < 200  # Should be < 200ms according to requirements


def test_health_endpoint_includes_all_required_services(client: TestClient):
    """Test that health endpoint includes all expected services."""
    response = client.get("/api/v1/health")

    data = response.json()

    # Should include all external services
    expected_services = {"efl_terminal", "cma_cgm", "openai", "twilio", "redis"}
    actual_services = set(data["services"].keys())

    assert expected_services.issubset(actual_services)
    assert all(status in ["up", "down", "degraded"] for status in data["services"].values())
