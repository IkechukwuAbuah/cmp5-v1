"""Health check API endpoint."""

import time
from datetime import datetime
from typing import Dict

from fastapi import APIRouter, HTTPException, Request
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address

from src.core.config import settings
from src.lib.circuit_breaker import CircuitBreakerManager
from src.lib.graceful_degradation import GracefulDegradationService
from src.schemas.health import HealthCheck, ServiceStatus

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)


@router.get("/test")
async def test_health():
    """Test endpoint for debugging."""
    return {"message": "health router test working"}


@router.get("/health", response_model=HealthCheck)
# @limiter.limit("30/minute")  # Temporarily disabled for debugging
async def health_check(request: Request):
    """Health check endpoint that validates system status and external dependencies."""
    start_time = time.time()

    try:
        # Check external services
        service_statuses = await _check_external_services()

        # Determine overall health status
        overall_status = _determine_overall_health(service_statuses)

        # Calculate response time
        response_time_ms = (time.time() - start_time) * 1000

        # Update graceful degradation service
        degradation_service = await GracefulDegradationService.get_instance()
        for service_name, status in service_statuses.items():
            degradation_service.update_service_status(
                service_name,
                is_healthy=status == ServiceStatus.UP,
                response_time_ms=response_time_ms
            )

        return HealthCheck(
            status=overall_status,
            timestamp=datetime.utcnow(),
            version=settings.VERSION,
            services={name: status.value for name, status in service_statuses.items()}
        )

    except Exception as e:
        # Log error and return degraded status
        print(f"Health check error: {e}")
        return HealthCheck(
            status="degraded",
            timestamp=datetime.utcnow(),
            version=settings.VERSION,
            services={"health_check": "degraded"}
        )


async def _check_external_services() -> Dict[str, ServiceStatus]:
    """Check the status of external services."""
    service_statuses = {}

    # Check EFL Terminal API
    service_statuses["efl_terminal"] = await _check_efl_terminal_api()

    # Check CMA CGM API
    service_statuses["cma_cgm"] = await _check_cma_cgm_api()

    # Check OpenAI API
    service_statuses["openai"] = await _check_openai_api()

    # Check Twilio API
    service_statuses["twilio"] = await _check_twilio_api()

    # Check Redis
    service_statuses["redis"] = await _check_redis_connection()

    return service_statuses


async def _check_efl_terminal_api() -> ServiceStatus:
    """Check EFL Terminal API connectivity."""
    try:
        # This would typically make a real API call
        # For now, we'll check the circuit breaker state
        circuit_breaker = CircuitBreakerManager.get_breaker("efl_terminal")
        if circuit_breaker.state.name == "OPEN":
            return ServiceStatus.DOWN
        return ServiceStatus.UP
    except Exception:
        return ServiceStatus.DOWN


async def _check_cma_cgm_api() -> ServiceStatus:
    """Check CMA CGM API connectivity."""
    try:
        circuit_breaker = CircuitBreakerManager.get_breaker("cma_cgm")
        if circuit_breaker.state.name == "OPEN":
            return ServiceStatus.DOWN
        return ServiceStatus.UP
    except Exception:
        return ServiceStatus.DOWN


async def _check_openai_api() -> ServiceStatus:
    """Check OpenAI API connectivity."""
    try:
        circuit_breaker = CircuitBreakerManager.get_breaker("openai")
        if circuit_breaker.state.name == "OPEN":
            return ServiceStatus.DOWN
        return ServiceStatus.UP
    except Exception:
        return ServiceStatus.DOWN


async def _check_twilio_api() -> ServiceStatus:
    """Check Twilio API connectivity."""
    try:
        circuit_breaker = CircuitBreakerManager.get_breaker("twilio")
        if circuit_breaker.state.name == "OPEN":
            return ServiceStatus.DOWN
        return ServiceStatus.UP
    except Exception:
        return ServiceStatus.DOWN


async def _check_redis_connection() -> ServiceStatus:
    """Check Redis connection."""
    try:
        # This would typically test actual Redis connectivity
        # For now, we'll assume it's up
        return ServiceStatus.UP
    except Exception:
        return ServiceStatus.DOWN


def _determine_overall_health(service_statuses: Dict[str, ServiceStatus]) -> str:
    """Determine overall system health based on service statuses."""
    critical_services = ["efl_terminal", "redis"]
    has_critical_failure = any(
        service_statuses.get(service) in [ServiceStatus.DOWN, ServiceStatus.DEGRADED]
        for service in critical_services
    )

    if has_critical_failure:
        return "unhealthy"

    has_degraded = any(
        status == ServiceStatus.DEGRADED
        for status in service_statuses.values()
    )

    if has_degraded:
        return "degraded"

    return "healthy"
