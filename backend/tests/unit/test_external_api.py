"""Unit tests for ExternalAPIService behavior."""

from datetime import datetime, timedelta
from typing import Any, Dict, List, Tuple
from unittest.mock import AsyncMock, Mock

import pytest

from src.core.config import settings
from src.lib.circuit_breaker import CircuitBreakerManager
from src.services.external_api_service import ExternalAPIService


class _AsyncResponseContext:
    """Simple async context manager to wrap mock responses."""

    def __init__(self, response: Any):
        self._response = response

    async def __aenter__(self) -> Any:
        return self._response

    async def __aexit__(self, exc_type, exc, tb) -> None:
        return None


class _BreakerStub:
    """Stub circuit breaker that returns a pre-built context manager."""

    def __init__(self, context: _AsyncResponseContext):
        self._context = context
        self.calls: List[Tuple[tuple, dict]] = []

    def call(self, *args, **kwargs):
        self.calls.append((args, kwargs))
        return self._context


@pytest.fixture
def service() -> ExternalAPIService:
    svc = ExternalAPIService()
    svc.degradation_service = Mock()
    return svc


def _build_response(status_code: int, payload: Dict[str, Any], elapsed_seconds: float = 0.12):
    response = Mock()
    response.status_code = status_code
    response.json = Mock(return_value=payload)
    response.elapsed = Mock()
    response.elapsed.total_seconds = Mock(return_value=elapsed_seconds)
    return response


def _mock_breaker(monkeypatch: pytest.MonkeyPatch, response: Any) -> _BreakerStub:
    breaker = _BreakerStub(_AsyncResponseContext(response))
    monkeypatch.setattr(CircuitBreakerManager, "get_breaker", lambda name: breaker)
    return breaker


@pytest.mark.asyncio
async def test_get_container_from_efl_terminal_success(monkeypatch: pytest.MonkeyPatch, service: ExternalAPIService):
    payload = {"containerNumber": "EFLU1234567"}
    response = _build_response(200, payload, elapsed_seconds=0.2)
    breaker = _mock_breaker(monkeypatch, response)

    result = await service.get_container_from_efl_terminal("EFLU1234567")

    assert result == payload
    assert len(breaker.calls) == 1
    args, kwargs = service.degradation_service.update_service_status.call_args
    assert args[0] == "efl_terminal"
    assert kwargs["is_healthy"] is True
    assert kwargs["response_time_ms"] == pytest.approx(200.0)


@pytest.mark.asyncio
async def test_get_container_from_efl_terminal_failure(monkeypatch: pytest.MonkeyPatch, service: ExternalAPIService):
    payload = {"error": "failure"}
    response = _build_response(500, payload)
    _mock_breaker(monkeypatch, response)

    result = await service.get_container_from_efl_terminal("EFLU7654321")

    assert result is None
    args, kwargs = service.degradation_service.update_service_status.call_args
    assert args[0] == "efl_terminal"
    assert kwargs["is_healthy"] is False
    assert "EFL Terminal API returned 500" in kwargs["error"]


@pytest.mark.asyncio
async def test_get_bl_from_cma_cgm_success(monkeypatch: pytest.MonkeyPatch, service: ExternalAPIService):
    payload = {"blNumber": "BL123"}
    response = _build_response(200, payload, elapsed_seconds=0.05)
    breaker = _mock_breaker(monkeypatch, response)

    result = await service.get_bl_from_cma_cgm("BL123")

    assert result == payload
    assert len(breaker.calls) == 1
    args, kwargs = service.degradation_service.update_service_status.call_args
    assert args[0] == "cma_cgm"
    assert kwargs["is_healthy"] is True
    assert kwargs["response_time_ms"] == pytest.approx(50.0)


@pytest.mark.asyncio
async def test_get_bl_from_cma_cgm_failure(monkeypatch: pytest.MonkeyPatch, service: ExternalAPIService):
    response = _build_response(404, {"message": "not found"})
    _mock_breaker(monkeypatch, response)

    result = await service.get_bl_from_cma_cgm("BL999")

    assert result is None
    args, kwargs = service.degradation_service.update_service_status.call_args
    assert args[0] == "cma_cgm"
    assert kwargs["is_healthy"] is False
    assert "CMA CGM API returned 404" in kwargs["error"]


@pytest.mark.asyncio
async def test_make_http_request_includes_service_headers(monkeypatch: pytest.MonkeyPatch, service: ExternalAPIService):
    client = AsyncMock()
    fake_response = Mock()
    client.request = AsyncMock(return_value=fake_response)
    service._client = client
    monkeypatch.setattr(settings, "EFL_TERMINAL_API_KEY", "efl-key", raising=False)
    monkeypatch.setattr(settings, "CMA_CGM_API_KEY", "cma-key", raising=False)

    await service._make_http_request(url="https://api.eflterminal.com/containers/EFLU123")
    _, kwargs = client.request.await_args
    headers = kwargs["headers"]
    assert headers["Authorization"] == "Bearer efl-key"

    client.request.reset_mock()
    await service._make_http_request(url="https://api.cma-cgm.com/bl/ABC123")
    _, kwargs = client.request.await_args
    headers = kwargs["headers"]
    assert headers["Authorization"] == "Bearer cma-key"


def test_format_container_data_defaults(service: ExternalAPIService):
    formatted = service.format_container_data({"containerNumber": "EFLU0000001"})

    assert formatted["containerNumber"] == "EFLU0000001"
    assert formatted["milestones"] == []
    assert "lastUpdated" in formatted


def test_format_bl_data_defaults(service: ExternalAPIService):
    formatted = service.format_bl_data({"blNumber": "BL321"})

    assert formatted["blNumber"] == "BL321"
    assert formatted["containers"] == []


def test_is_data_fresh(service: ExternalAPIService):
    fresh_timestamp = datetime.utcnow().isoformat()
    stale_timestamp = (datetime.utcnow() - timedelta(hours=2)).isoformat()

    assert service.is_data_fresh(fresh_timestamp) is True
    assert service.is_data_fresh(stale_timestamp, max_age_minutes=30) is False
    assert service.is_data_fresh("invalid-timestamp") is False


@pytest.mark.asyncio
async def test_get_service_health(monkeypatch: pytest.MonkeyPatch, service: ExternalAPIService):
    def _make_breaker(state_name: str, failure_count: int):
        breaker = Mock()
        state = Mock()
        state.value = state_name.lower()
        state.name = state_name.upper()
        breaker.state = state
        breaker.failure_count = failure_count
        return breaker

    breakers = {
        "efl_terminal": _make_breaker("closed", 0),
        "cma_cgm": _make_breaker("open", 3),
        "openai": _make_breaker("half_open", 1),
        "twilio": _make_breaker("closed", 0),
    }

    monkeypatch.setattr(CircuitBreakerManager, "get_breaker", lambda name: breakers[name])

    health = await service.get_service_health()

    assert health["efl_terminal"]["is_healthy"] is True
    assert health["cma_cgm"]["is_healthy"] is False
    assert health["cma_cgm"]["state"] == "open"
    assert health["openai"]["state"] == "half_open"
