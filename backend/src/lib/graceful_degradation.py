"""Graceful degradation service for handling API failures."""

import asyncio
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from enum import Enum

from src.core.config import settings
from src.lib.circuit_breaker import CircuitBreakerManager


class DegradationLevel(Enum):
    """Levels of service degradation."""
    FULL_SERVICE = "full_service"        # All services operational
    PARTIAL_SERVICE = "partial_service"  # Some services degraded
    MINIMAL_SERVICE = "minimal_service"  # Core functionality only
    OFFLINE = "offline"                  # Service unavailable


@dataclass
class ServiceStatus:
    """Status of a specific service."""
    name: str
    is_healthy: bool = True
    last_check: float = field(default_factory=time.time)
    error_count: int = 0
    response_time_ms: float = 0.0
    last_error: Optional[str] = None


class GracefulDegradationService:
    """Service for managing graceful degradation."""

    _instance: Optional["GracefulDegradationService"] = None
    _lock: asyncio.Lock = asyncio.Lock()

    def __init__(self):
        self._services: Dict[str, ServiceStatus] = {}
        self._degradation_level: DegradationLevel = DegradationLevel.FULL_SERVICE
        self._fallback_cache: Dict[str, Any] = {}
        self._cache_timestamps: Dict[str, float] = {}

    @classmethod
    async def get_instance(cls) -> "GracefulDegradationService":
        """Get singleton instance."""
        if cls._instance is None:
            async with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance

    def register_service(self, name: str) -> None:
        """Register a service for monitoring."""
        if name not in self._services:
            self._services[name] = ServiceStatus(name)

    def update_service_status(
        self,
        name: str,
        is_healthy: bool,
        response_time_ms: float = 0.0,
        error: Optional[str] = None
    ) -> None:
        """Update service status."""
        if name not in self._services:
            self.register_service(name)

        service = self._services[name]
        service.is_healthy = is_healthy
        service.last_check = time.time()
        service.response_time_ms = response_time_ms

        if not is_healthy:
            service.error_count += 1
            service.last_error = error
        else:
            service.error_count = 0
            service.last_error = None

        self._update_degradation_level()

    def _update_degradation_level(self) -> None:
        """Update overall degradation level based on service statuses."""
        if not self._services:
            return

        unhealthy_services = [s for s in self._services.values() if not s.is_healthy]
        total_services = len(self._services)

        if len(unhealthy_services) == 0:
            self._degradation_level = DegradationLevel.FULL_SERVICE
        elif len(unhealthy_services) < total_services * 0.5:
            self._degradation_level = DegradationLevel.PARTIAL_SERVICE
        elif len(unhealthy_services) < total_services * 0.8:
            self._degradation_level = DegradationLevel.MINIMAL_SERVICE
        else:
            self._degradation_level = DegradationLevel.OFFLINE

    def get_degradation_level(self) -> DegradationLevel:
        """Get current degradation level."""
        return self._degradation_level

    def is_service_available(self, service_name: str) -> bool:
        """Check if a service is available (considering circuit breakers)."""
        if service_name not in self._services:
            return False

        service = self._services[service_name]

        # Check circuit breaker state
        circuit_breaker = CircuitBreakerManager.get_breaker(service_name)
        if circuit_breaker.state.name == "OPEN":
            return False

        return service.is_healthy

    def can_use_fallback(self, service_name: str, data_key: str) -> bool:
        """Check if fallback data can be used for a service."""
        if not settings.ENABLE_FALLBACK_TO_CACHE:
            return False

        if data_key not in self._fallback_cache:
            return False

        # Check if cache is still fresh
        cache_time = self._cache_timestamps.get(data_key, 0)
        age_minutes = (time.time() - cache_time) / 60

        return age_minutes <= settings.CACHE_STALENESS_TOLERANCE_MINUTES

    def get_fallback_data(self, data_key: str) -> Optional[Any]:
        """Get fallback data if available and fresh."""
        if not self.can_use_fallback(data_key):
            return None

        return self._fallback_cache[data_key]

    def set_fallback_data(self, data_key: str, data: Any) -> None:
        """Cache fallback data."""
        self._fallback_cache[data_key] = data
        self._cache_timestamps[data_key] = time.time()

    def get_service_status_report(self) -> Dict[str, Any]:
        """Get comprehensive service status report."""
        return {
            "degradation_level": self._degradation_level.value,
            "services": {
                name: {
                    "healthy": status.is_healthy,
                    "error_count": status.error_count,
                    "response_time_ms": status.response_time_ms,
                    "last_error": status.last_error,
                    "last_check": status.last_check
                }
                for name, status in self._services.items()
            },
            "timestamp": time.time()
        }

    async def health_check_all_services(self) -> Dict[str, bool]:
        """Perform health check on all registered services."""
        results = {}

        for service_name in self._services.keys():
            # This would typically involve actual health checks
            # For now, we'll use the stored status
            results[service_name] = self._services[service_name].is_healthy

        return results
