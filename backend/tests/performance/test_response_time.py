"""Performance regression tests validating API response times (T067)."""

from __future__ import annotations

from time import perf_counter
from types import SimpleNamespace
from typing import Any, Dict, Tuple

import pytest
from fastapi.testclient import TestClient

from src.core.config import settings
from src.main import create_application
from src.middleware.auth import create_access_token, get_current_agent
from src.models.agent import ChannelType, Agent, AgentType, ContactInfo, Permission
from src.services.session_service import SessionService


@pytest.fixture(scope="module")
def client() -> TestClient:
    """Instantiate a FastAPI test client for performance assertions."""
    app = create_application()

    agent = Agent(
        id="performance-agent",
        name="Performance Agent",
        type=AgentType.CLEARING,
        contactInfo=ContactInfo(
            phone="+2347010000000",
            email="perf@efl.com",
            companyName="EFL Test Logistics",
        ),
        permissions=[
            Permission(resource="container", actions=["read", "track"], conditions=None),
            Permission(resource="bl", actions=["read", "track"], conditions=None),
            Permission(resource="session", actions=["read", "write"], conditions=None),
        ],
    )

    def _override_current_agent() -> Agent:
        return agent

    app.dependency_overrides[get_current_agent] = _override_current_agent
    return TestClient(app)


@pytest.fixture(autouse=True)
def stub_session_service(monkeypatch: pytest.MonkeyPatch) -> None:
    """Stub SessionService to avoid Redis dependency during performance runs."""

    class _StubSessionService:
        def __init__(self) -> None:
            self._session_counter = 0
            self._language = settings.DEFAULT_LANGUAGE
            self._culture = settings.DEFAULT_CULTURAL_CONTEXT

        async def create_session(self, agent_id: str, channel: ChannelType) -> SimpleNamespace:
            self._session_counter += 1
            session_id = f"perf-session-{self._session_counter}"
            return SimpleNamespace(id=session_id)

        async def add_message(self, session_id: str, message) -> bool:  # pragma: no cover - trivial stub
            return True

        async def update_localisation_preferences(
            self,
            session_id: str,
            agent_id: str,
            *,
            language: str | None = None,
            cultural_context: str | None = None,
        ) -> bool:
            if language:
                self._language = language
            if cultural_context:
                self._culture = cultural_context
            return True

        async def update_cultural_preference(
            self,
            session_id: str,
            agent_id: str,
            preference: str,
        ) -> bool:
            self._culture = preference
            return True

        async def get_language_preference(self, session_id: str | None, agent_id: str | None = None) -> str:
            return self._language

        async def get_cultural_preference(self, session_id: str | None, agent_id: str | None = None) -> str:
            return self._culture

    stub = _StubSessionService()

    async def _get_instance(_self) -> _StubSessionService:
        return stub

    monkeypatch.setattr(SessionService, "get_instance", _get_instance, raising=False)


@pytest.fixture(scope="module")
def auth_headers() -> Dict[str, str]:
    """Generate Authorization headers for protected endpoints."""
    token = create_access_token({"sub": "agent_performance", "role": "clearing"})
    return {"Authorization": f"Bearer {token}"}


def _measure_request(callable_, *args, **kwargs) -> Tuple[float, Any]:
    """Execute request callable and return (duration_ms, response)."""
    start = perf_counter()
    response = callable_(*args, **kwargs)
    duration_ms = (perf_counter() - start) * 1000
    return duration_ms, response


@pytest.mark.performance
def test_health_endpoint_within_latency_budget(client: TestClient) -> None:
    duration_ms, response = _measure_request(client.get, "/api/v1/health")

    assert response.status_code == 200
    assert duration_ms <= settings.MAX_RESPONSE_TIME_MS


@pytest.mark.performance
def test_track_endpoint_within_latency_budget(client: TestClient, auth_headers: Dict[str, str]) -> None:
    payload = {
        "query": "Track container EFLU1234567",
        "channel": ChannelType.CHAT.value,
        "agentId": "agent_performance",
    }

    duration_ms, response = _measure_request(
        client.post,
        "/api/v1/track",
        json=payload,
        headers=auth_headers,
    )

    assert response.status_code == 200
    assert duration_ms <= settings.MAX_RESPONSE_TIME_MS

    body = response.json()
    assert body.get("sessionId")
    assert body.get("metadata", {}).get("processing_time_ms", settings.MAX_RESPONSE_TIME_MS) <= settings.MAX_RESPONSE_TIME_MS


@pytest.mark.performance
def test_container_endpoint_within_latency_budget(client: TestClient, auth_headers: Dict[str, str]) -> None:
    duration_ms, response = _measure_request(
        client.get,
        "/api/v1/containers/EFLU1234567",
        headers=auth_headers,
    )

    assert response.status_code == 200
    assert duration_ms <= settings.MAX_RESPONSE_TIME_MS


@pytest.mark.performance
def test_bill_of_lading_endpoint_within_latency_budget(client: TestClient, auth_headers: Dict[str, str]) -> None:
    duration_ms, response = _measure_request(
        client.get,
        "/api/v1/bl/ABC1234567",
        headers=auth_headers,
    )

    assert response.status_code == 200
    assert duration_ms <= settings.MAX_RESPONSE_TIME_MS
