"""TrackService for container and bill of lading tracking logic."""

import time
import re
from typing import Dict, List, Optional, Tuple
from datetime import datetime

from src.core.config import settings
from src.models.agent import Agent
from src.models.bill_of_lading import BillOfLading
from src.models.container import Container, ContainerStatus
from src.models.terminal_location import TerminalLocation
from src.lib.circuit_breaker import CircuitBreakerManager
from src.lib.graceful_degradation import GracefulDegradationService


class TrackService:
    """Service for tracking containers and bill of ladings with natural language processing."""

    def __init__(self):
        self.degradation_service = None

    async def get_instance(self) -> "TrackService":
        """Get singleton instance with dependencies initialized."""
        if self.degradation_service is None:
            self.degradation_service = await GracefulDegradationService.get_instance()
        return self

    async def track_container(self, container_id: str, agent: Agent) -> Optional[Container]:
        """Track a specific container by ID."""
        # Check agent permissions
        if not agent.can_access_container(container_id):
            return None

        # Try EFL Terminal API first
        container = await self._get_container_from_efl_terminal(container_id)

        if container:
            return container

        # Fallback to CMA CGM API
        container = await self._get_container_from_cma_cgm(container_id)

        if container:
            return container

        # Fallback to cached data if available
        return await self._get_container_from_cache(container_id, agent)

    async def track_bl(self, bl_number: str, agent: Agent) -> Optional[BillOfLading]:
        """Track a bill of lading by number."""
        # Check agent permissions
        if not agent.can_access_bl(bl_number):
            return None

        # Try CMA CGM API first
        bl = await self._get_bl_from_cma_cgm(bl_number)

        if bl:
            return bl

        # Fallback to EFL Terminal API
        bl = await self._get_bl_from_efl_terminal(bl_number)

        if bl:
            return bl

        return None

    async def process_natural_language_query(self, query: str, agent: Agent) -> Dict:
        """Process natural language tracking query and return structured results."""
        # Extract entities from natural language
        entities = self._extract_entities(query)

        containers = []
        bill_of_ladings = []

        # Track containers
        for entity in entities.get("containers", []):
            container = await self.track_container(entity, agent)
            if container:
                containers.append(container)

        # Track bill of ladings
        for entity in entities.get("bill_of_ladings", []):
            bl = await self.track_bl(entity, agent)
            if bl:
                bill_of_ladings.append(bl)

        return {
            "containers": containers,
            "bill_of_ladings": bill_of_ladings,
            "entities": entities
        }

    def _extract_entities(self, query: str) -> Dict[str, List[str]]:
        """Extract container IDs and BL numbers from natural language query."""
        entities = {
            "containers": [],
            "bill_of_ladings": []
        }

        # Extract container IDs (EFLU followed by 7 digits)
        container_pattern = r'EFLU\d{7}'
        containers = re.findall(container_pattern, query.upper())
        entities["containers"] = containers

        # Extract BL numbers (ABC followed by 7 digits)
        bl_pattern = r'ABC\d{7}'
        bl_numbers = re.findall(bl_pattern, query.upper())
        entities["bill_of_ladings"] = bl_numbers

        return entities

    async def _get_container_from_efl_terminal(self, container_id: str) -> Optional[Container]:
        """Get container data from EFL Terminal API."""
        try:
            circuit_breaker = CircuitBreakerManager.get_breaker("efl_terminal")

            # This would make actual API call to EFL Terminal
            # For now, return mock data
            return Container(
                id=container_id,
                containerNumber=container_id,
                isoCode="45G1",
                status=ContainerStatus.AT_TERMINAL,
                location=TerminalLocation(
                    id="loc_1",
                    name="Yard A1",
                    type="yard",
                    coordinates={"latitude": 6.4474, "longitude": 3.3903},
                    terminalId="efl_terminal",
                    isActive=True
                ),
                billOfLading=BillOfLading(
                    id="BL123",
                    blNumber="ABC1234567",
                    vesselVoyage={
                        "id": "voy_1",
                        "vesselName": "Marco Polo",
                        "voyageNumber": "12345",
                        "carrier": "CMA CGM",
                        "originPort": "Lagos Port",
                        "destinationPort": "EFL Terminal, Ikorodu",
                        "estimatedDeparture": datetime.now(),
                        "estimatedArrival": datetime.now(),
                        "status": "in_transit"
                    },
                    origin="Lagos",
                    destination="Ikorodu",
                    estimatedArrival=datetime.now(),
                    shippingLine="CMA CGM",
                    agentId="agent_123"
                ),
                agentId="agent_123",
                milestones=[],
                lastUpdated=time.time(),
                nextStep="Awaiting customs examination booking"
            )

        except Exception as e:
            print(f"Error getting container from EFL Terminal: {e}")
            return None

    async def _get_container_from_cma_cgm(self, container_id: str) -> Optional[Container]:
        """Get container data from CMA CGM API."""
        try:
            circuit_breaker = CircuitBreakerManager.get_breaker("cma_cgm")

            # This would make actual API call to CMA CGM
            # For now, return None to trigger fallback
            return None

        except Exception as e:
            print(f"Error getting container from CMA CGM: {e}")
            return None

    async def _get_container_from_cache(self, container_id: str, agent: Agent) -> Optional[Container]:
        """Get container data from cache if available and fresh."""
        cache_key = f"container:{container_id}:{agent.id}"

        if self.degradation_service and self.degradation_service.can_use_fallback("container_cache", cache_key):
            cached_data = self.degradation_service.get_fallback_data(cache_key)
            if cached_data:
                return Container(**cached_data)

        return None

    async def _get_bl_from_cma_cgm(self, bl_number: str) -> Optional[BillOfLading]:
        """Get bill of lading data from CMA CGM API."""
        try:
            circuit_breaker = CircuitBreakerManager.get_breaker("cma_cgm")

            # This would make actual API call to CMA CGM
            # For now, return mock data
            return BillOfLading(
                id=bl_number,
                blNumber=bl_number,
                vesselVoyage={
                    "id": "voy_1",
                    "vesselName": "Marco Polo",
                    "voyageNumber": "12345",
                    "carrier": "CMA CGM",
                    "originPort": "Lagos Port",
                    "destinationPort": "EFL Terminal, Ikorodu",
                    "estimatedDeparture": datetime.now(),
                    "estimatedArrival": datetime.now(),
                    "status": "in_transit"
                },
                origin="Lagos",
                destination="Ikorodu",
                estimatedArrival=datetime.now(),
                shippingLine="CMA CGM",
                agentId="agent_123"
            )

        except Exception as e:
            print(f"Error getting BL from CMA CGM: {e}")
            return None

    async def _get_bl_from_efl_terminal(self, bl_number: str) -> Optional[BillOfLading]:
        """Get bill of lading data from EFL Terminal API."""
        try:
            circuit_breaker = CircuitBreakerManager.get_breaker("efl_terminal")

            # This would make actual API call to EFL Terminal
            # For now, return None to trigger fallback
            return None

        except Exception as e:
            print(f"Error getting BL from EFL Terminal: {e}")
            return None

    def determine_next_step(self, containers: List[Container]) -> str:
        """Determine the next step for the user based on container statuses."""
        if not containers:
            return "Please provide a valid container number or bill of lading number."

        container = containers[0]

        if container.status == ContainerStatus.AT_TERMINAL:
            return "You may now book a customs examination."
        elif container.status == ContainerStatus.CLEARED_FOR_EXAM:
            return "Customs examination has been scheduled. Please wait for inspection."
        elif container.status == ContainerStatus.RELEASED:
            return "Container is ready for pickup."
        elif container.status == ContainerStatus.IN_TRANSIT:
            return f"Container is in transit. Expected arrival: {container.billOfLading.estimatedArrival}"
        else:
            return f"Current status: {container.status.replace('_', ' ').title()}. Contact EFL Terminal for next steps."
