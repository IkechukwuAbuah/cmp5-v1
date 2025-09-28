"""Contract tests ensuring cultural error payloads are returned."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from src.main import create_application
from src.middleware.auth import get_current_agent
from src.models.agent import Agent, AgentType, ContactInfo, Permission
from src.services.track_service import TrackService


@pytest.fixture()
def client():
    test_app = create_application()
    with TestClient(test_app) as test_client:
        yield test_client


def _make_agent(permissions: list[Permission]) -> Agent:
    return Agent(
        id="agent_test",
        name="Test Agent",
        type=AgentType.CLEARING,
        contactInfo=ContactInfo(
            phone="+2341112222",
            email="agent@test.com",
            companyName="Test Logistics"
        ),
        permissions=permissions,
        sessionHistory=[],
    )


def test_container_permission_denied_returns_cultural_payload(client, restore_overrides):
    def override_agent():
        return _make_agent(permissions=[])

    client.app.dependency_overrides[get_current_agent] = override_agent
    try:
        response = client.get(
            "/api/v1/containers/EFLU1234567",
            headers={"Accept-Language": "en-NG"}
        )

        assert response.status_code == 403
        payload = response.json()
        _assert_cultural_payload(payload)
        assert payload["culturalContext"] == "nigerian"
        assert response.headers["X-Localisation-Cultural-Context"] == "nigerian"
        assert "X-Localisation-Latency" in response.headers
    finally:
        client.app.dependency_overrides.clear()


def test_track_system_error_returns_cultural_payload(client, restore_overrides, monkeypatch):
    def override_agent():
        return _make_agent(
            permissions=[Permission(resource="container", actions=["read"], conditions=None)]
        )

    client.app.dependency_overrides[get_current_agent] = override_agent

    async def failing_query(self, query: str, agent: Agent):  # type: ignore[override]
        raise RuntimeError("boom")

    monkeypatch.setattr(TrackService, "process_natural_language_query", failing_query, raising=False)

    try:
        response = client.post(
            "/api/v1/track",
            json={
                "query": "Track container XYZ",
                "channel": "chat",
                "sessionId": "",
                "agentId": "agent_test"
            },
            headers={"Accept-Language": "fr-SN"}
        )

        assert response.status_code == 500
        payload = response.json()
        _assert_cultural_payload(payload)
        assert payload["error"] == "SYSTEM_UNAVAILABLE"
        assert response.headers["X-Localisation-Cultural-Context"] in {"nigerian", "west_african", "formal_business"}
    finally:
        client.app.dependency_overrides.clear()


def _assert_cultural_payload(payload: dict) -> None:
    expected_keys = {
        "error",
        "message",
        "alternatives",
        "nextSteps",
        "tone",
        "requiresConfirmation",
        "culturalContext",
        "timestamp",
        "source",
    }
    assert expected_keys.issubset(payload.keys())
    assert isinstance(payload["alternatives"], list)
    assert isinstance(payload["nextSteps"], list)
