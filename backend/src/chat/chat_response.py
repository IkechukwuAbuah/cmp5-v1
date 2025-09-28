"""Chat response formatting service matching voice quality."""

from __future__ import annotations

from datetime import datetime
from typing import Dict, List, Optional

from src.models.agent import ChannelType
from src.models.bill_of_lading import BillOfLading
from src.models.container import Container
from src.services.response_service import ResponseService


class ChatResponseFormatter:
    """Format chat responses with parity to voice experience."""

    def __init__(self):
        self.response_service: Optional[ResponseService] = None

    async def get_instance(self) -> "ChatResponseFormatter":
        if self.response_service is None:
            self.response_service = await ResponseService().get_instance()
        return self

    def build_tracking_reply(
        self,
        query: str,
        containers: List[Container],
        bill_of_ladings: List[BillOfLading],
        entities: Dict,
    ) -> Dict[str, Optional[str]]:
        """Create a rich tracking reply with follow-up suggestions."""

        message = self.response_service.format_tracking_response(
            query=query,
            containers=containers,
            bill_of_ladings=bill_of_ladings,
            channel=ChannelType.CHAT,
        )

        summary = self._build_summary(containers, bill_of_ladings)
        suggestions = self._build_follow_up_suggestions(containers, bill_of_ladings, entities)

        return {
            "message": message,
            "summary": summary,
            "suggestions": suggestions,
        }

    def format_error(self, error: str) -> str:
        return self.response_service.format_error_response(error, ChannelType.CHAT)

    def format_help(self) -> str:
        return self.response_service.format_help_response(ChannelType.CHAT)

    def _build_summary(
        self, containers: List[Container], bill_of_ladings: List[BillOfLading]
    ) -> Optional[str]:
        if containers:
            container = containers[0]
            parts = [f"Status: {container.status.value.replace('_', ' ').title()}"]
            if container.location:
                parts.append(f"Location: {self._format_location(container.location)}")
            if container.nextStep:
                parts.append(f"Next: {container.nextStep}")
            return " | ".join(parts)

        if bill_of_ladings:
            bl = bill_of_ladings[0]
            parts = [f"Route: {bl.origin} → {bl.destination}"]
            if bl.estimatedArrival and isinstance(bl.estimatedArrival, datetime):
                parts.append(f"ETA: {bl.estimatedArrival.strftime('%Y-%m-%d %H:%M UTC')}")
            return " | ".join(parts)

        return None

    def _build_follow_up_suggestions(
        self,
        containers: List[Container],
        bill_of_ladings: List[BillOfLading],
        entities: Dict,
    ) -> List[str]:
        suggestions: List[str] = []

        if containers:
            first = containers[0]
            suggestions.extend(
                [
                    f"Show milestones for {first.containerNumber}",
                    f"What is the next step for {first.containerNumber}?",
                ]
            )

        if bill_of_ladings:
            bl = bill_of_ladings[0]
            suggestions.append(f"List containers for {bl.blNumber}")

        if not suggestions and entities:
            container_entities = entities.get("containers", [])
            bl_entities = entities.get("bill_of_ladings", [])
            if container_entities:
                suggestions.append(f"Track container {container_entities[0]}")
            if bl_entities:
                suggestions.append(f"Track BL {bl_entities[0]}")

        if not suggestions:
            suggestions.append("Help")

        return suggestions

    def _format_location(self, location: Dict) -> str:
        if isinstance(location, dict):
            name = location.get("name")
            terminal = location.get("terminalId")
            if name and terminal:
                return f"{name}, {terminal}"
            return name or terminal or "Unknown"
        return str(location)


__all__ = ["ChatResponseFormatter"]
