"""ExternalAPIService for EFL Terminal and CMA CGM API integration."""

import asyncio
import httpx
from typing import Dict, List, Optional, Any
from datetime import datetime

from src.core.config import settings
from src.lib.circuit_breaker import CircuitBreakerManager
from src.lib.graceful_degradation import GracefulDegradationService


class ExternalAPIService:
    """Service for integrating with external APIs (EFL Terminal, CMA CGM)."""

    def __init__(self):
        self.degradation_service = None
        self._client = None

    async def get_instance(self) -> "ExternalAPIService":
        """Get singleton instance with dependencies initialized."""
        if self.degradation_service is None:
            self.degradation_service = await GracefulDegradationService.get_instance()
        return self

    async def get_container_from_efl_terminal(self, container_id: str) -> Optional[Dict]:
        """Get container data from EFL Terminal API."""
        try:
            circuit_breaker = CircuitBreakerManager.get_breaker("efl_terminal")

            async with circuit_breaker.call(self._make_http_request) as response:
                if response.status_code == 200:
                    data = response.json()

                    # Update service health
                    self.degradation_service.update_service_status(
                        "efl_terminal",
                        is_healthy=True,
                        response_time_ms=response.elapsed.total_seconds() * 1000
                    )

                    return data
                else:
                    raise Exception(f"EFL Terminal API returned {response.status_code}")

        except Exception as e:
            # Update service health
            self.degradation_service.update_service_status(
                "efl_terminal",
                is_healthy=False,
                error=str(e)
            )
            return None

    async def get_container_from_cma_cgm(self, container_id: str) -> Optional[Dict]:
        """Get container data from CMA CGM API."""
        try:
            circuit_breaker = CircuitBreakerManager.get_breaker("cma_cgm")

            async with circuit_breaker.call(self._make_http_request) as response:
                if response.status_code == 200:
                    data = response.json()

                    # Update service health
                    self.degradation_service.update_service_status(
                        "cma_cgm",
                        is_healthy=True,
                        response_time_ms=response.elapsed.total_seconds() * 1000
                    )

                    return data
                else:
                    raise Exception(f"CMA CGM API returned {response.status_code}")

        except Exception as e:
            # Update service health
            self.degradation_service.update_service_status(
                "cma_cgm",
                is_healthy=False,
                error=str(e)
            )
            return None

    async def get_bl_from_cma_cgm(self, bl_number: str) -> Optional[Dict]:
        """Get bill of lading data from CMA CGM API."""
        try:
            circuit_breaker = CircuitBreakerManager.get_breaker("cma_cgm")

            async with circuit_breaker.call(self._make_http_request) as response:
                if response.status_code == 200:
                    data = response.json()

                    # Update service health
                    self.degradation_service.update_service_status(
                        "cma_cgm",
                        is_healthy=True,
                        response_time_ms=response.elapsed.total_seconds() * 1000
                    )

                    return data
                else:
                    raise Exception(f"CMA CGM API returned {response.status_code}")

        except Exception as e:
            # Update service health
            self.degradation_service.update_service_status(
                "cma_cgm",
                is_healthy=False,
                error=str(e)
            )
            return None

    async def get_bl_from_efl_terminal(self, bl_number: str) -> Optional[Dict]:
        """Get bill of lading data from EFL Terminal API."""
        try:
            circuit_breaker = CircuitBreakerManager.get_breaker("efl_terminal")

            async with circuit_breaker.call(self._make_http_request) as response:
                if response.status_code == 200:
                    data = response.json()

                    # Update service health
                    self.degradation_service.update_service_status(
                        "efl_terminal",
                        is_healthy=True,
                        response_time_ms=response.elapsed.total_seconds() * 1000
                    )

                    return data
                else:
                    raise Exception(f"EFL Terminal API returned {response.status_code}")

        except Exception as e:
            # Update service health
            self.degradation_service.update_service_status(
                "efl_terminal",
                is_healthy=False,
                error=str(e)
            )
            return None

    async def _make_http_request(self, method: str = "GET", url: str = "", **kwargs) -> httpx.Response:
        """Make HTTP request with proper headers and authentication."""
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "EFL-Agent-Assistant/1.0.0"
        }

        # Add API keys if configured
        if "efl" in url.lower():
            if settings.EFL_TERMINAL_API_KEY:
                headers["Authorization"] = f"Bearer {settings.EFL_TERMINAL_API_KEY}"
        elif "cma" in url.lower():
            if settings.CMA_CGM_API_KEY:
                headers["Authorization"] = f"Bearer {settings.CMA_CGM_API_KEY}"

        client = await self._get_http_client()

        return await client.request(method, url, headers=headers, **kwargs)

    async def _get_http_client(self) -> httpx.AsyncClient:
        """Get HTTP client with proper configuration."""
        if self._client is None:
            self._client = httpx.AsyncClient(
                timeout=30.0,  # 30 second timeout
                limits=httpx.Limits(
                    max_keepalive_connections=20,
                    max_connections=100
                )
            )
        return self._client

    def format_container_data(self, raw_data: Dict) -> Dict:
        """Format raw container data into standardized format."""
        return {
            "containerNumber": raw_data.get("containerNumber", ""),
            "isoCode": raw_data.get("isoCode", ""),
            "status": raw_data.get("status", ""),
            "location": raw_data.get("location", {}),
            "billOfLading": raw_data.get("billOfLading", {}),
            "milestones": raw_data.get("milestones", []),
            "lastUpdated": raw_data.get("lastUpdated", datetime.utcnow().isoformat()),
            "nextStep": raw_data.get("nextStep", "")
        }

    def format_bl_data(self, raw_data: Dict) -> Dict:
        """Format raw bill of lading data into standardized format."""
        return {
            "blNumber": raw_data.get("blNumber", ""),
            "vesselVoyage": raw_data.get("vesselVoyage", {}),
            "origin": raw_data.get("origin", ""),
            "destination": raw_data.get("destination", ""),
            "estimatedArrival": raw_data.get("estimatedArrival", ""),
            "actualArrival": raw_data.get("actualArrival", ""),
            "shippingLine": raw_data.get("shippingLine", ""),
            "containers": raw_data.get("containers", [])
        }

    def is_data_fresh(self, data_timestamp: str, max_age_minutes: int = 60) -> bool:
        """Check if data is fresh enough to use."""
        try:
            data_time = datetime.fromisoformat(data_timestamp.replace('Z', '+00:00'))
            age = datetime.utcnow() - data_time.replace(tzinfo=None)
            return age.total_seconds() < (max_age_minutes * 60)
        except:
            return False

    async def get_service_health(self) -> Dict[str, Any]:
        """Get health status of all external services."""
        services = ["efl_terminal", "cma_cgm", "openai", "twilio"]

        health_status = {}
        for service in services:
            circuit_breaker = CircuitBreakerManager.get_breaker(service)
            health_status[service] = {
                "state": circuit_breaker.state.value,
                "failure_count": circuit_breaker.failure_count,
                "is_healthy": circuit_breaker.state.name != "OPEN"
            }

        return health_status
