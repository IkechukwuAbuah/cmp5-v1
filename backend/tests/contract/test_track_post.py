"""Contract tests for POST /track endpoint."""

import pytest
from fastapi.testclient import TestClient
import time


def test_track_endpoint_accepts_valid_request(client: TestClient):
    """Test that track endpoint accepts valid TrackRequest."""
    request_data = {
        "query": "Track container EFLU7896543",
        "channel": "chat",
        "agentId": "agent_123"  # Fixed field name
    }

    response = client.post("/api/v1/track", json=request_data)

    # Debug: print response details if failing
    if response.status_code != 200:
        print(f"Response status: {response.status_code}")
        print(f"Response content: {response.text}")

    assert response.status_code == 200

    data = response.json()
    assert "sessionId" in data
    assert "response" in data
    assert "containers" in data
    assert "billOfLadings" in data
    assert "nextStep" in data
    assert "followUp" in data
    assert "confidence" in data
    assert "metadata" in data


def test_track_endpoint_returns_valid_response(client: TestClient):
    """Test that track endpoint returns valid TrackResponse."""
    request_data = {
        "query": "What's the status of container EFLU7896543?",
        "channel": "chat",
        "agentId": "agent_123"  # Fixed field name
    }

    response = client.post("/api/v1/track", json=request_data)

    data = response.json()

    # Check response structure
    assert isinstance(data["sessionId"], str)
    assert isinstance(data["response"], str)
    assert isinstance(data["containers"], list)
    assert isinstance(data["billOfLadings"], list)
    assert isinstance(data["nextStep"], str)
    assert isinstance(data["followUp"], bool)
    assert isinstance(data["confidence"], float)
    assert isinstance(data["metadata"], dict)

    # Check confidence range
    assert 0.0 <= data["confidence"] <= 1.0


def test_track_endpoint_handles_voice_channel(client: TestClient):
    """Test that track endpoint properly handles voice channel requests."""
    request_data = {
        "query": "Track my container",
        "channel": "voice",
        "agentId": "agent_123"  # Fixed field name
    }

    response = client.post("/api/v1/track", json=request_data)

    assert response.status_code == 200
    data = response.json()
    assert "response" in data
    # Voice responses should be suitable for text-to-speech


def test_track_endpoint_handles_chat_channel(client: TestClient):
    """Test that track endpoint properly handles chat channel requests."""
    request_data = {
        "query": "Track container",
        "channel": "chat",
        "agentId": "agent_123"  # Fixed field name
    }

    response = client.post("/api/v1/track", json=request_data)

    assert response.status_code == 200
    data = response.json()
    assert "response" in data
    # Chat responses should be optimized for text display


def test_track_endpoint_handles_missing_agent_id(client: TestClient):
    """Test that track endpoint requires agentId."""
    request_data = {
        "query": "Track container EFLU7896543",
        "channel": "chat"
        # Missing agentId
    }

    response = client.post("/api/v1/track", json=request_data)

    # Should return 422 for missing required field
    assert response.status_code == 422


def test_track_endpoint_handles_invalid_channel(client: TestClient):
    """Test that track endpoint validates channel values."""
    request_data = {
        "query": "Track container",
        "channel": "invalid_channel",
        "agentId": "agent_123"  # Fixed field name
    }

    response = client.post("/api/v1/track", json=request_data)

    # Should return 422 for invalid channel value
    assert response.status_code == 422


def test_track_endpoint_response_time_under_five_seconds(client: TestClient):
    """Test that track endpoint responds within 5 seconds."""
    request_data = {
        "query": "Track container EFLU7896543",
        "channel": "chat",
        "agentId": "agent_123"  # Fixed field name
    }

    start_time = time.time()
    response = client.post("/api/v1/track", json=request_data)
    end_time = time.time()

    response_time = end_time - start_time

    assert response.status_code == 200
    assert response_time < 5  # Should be < 5 seconds according to requirements
