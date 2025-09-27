"""Voice response formatting service for EFL Agent Assistant."""

import re
import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime

from src.models.agent import ChannelType, Message
from src.services.response_service import ResponseService
from src.services.track_service import TrackService
from src.models.container import Container, BillOfLading, ContainerStatus


logger = logging.getLogger(__name__)


class VoiceResponseFormatter:
    """Service for formatting responses specifically for voice delivery."""

    def __init__(self):
        self.response_service = None
        self.track_service = None

    async def get_instance(self) -> "VoiceResponseFormatter":
        """Get singleton instance with dependencies initialized."""
        if self.response_service is None:
            self.response_service = await ResponseService().get_instance()
        if self.track_service is None:
            self.track_service = await TrackService().get_instance()
        return self

    def format_voice_response(
        self,
        query: str,
        containers: List[Container],
        bill_of_ladings: List[BillOfLading],
        context: Dict[str, Any] = None
    ) -> str:
        """Format a response specifically for voice delivery."""
        if not containers and not bill_of_ladings:
            return self._format_no_results_voice(query)

        # Determine the primary focus
        if containers:
            return self._format_containers_voice(containers, query)
        elif bill_of_ladings:
            return self._format_bill_of_lading_voice(bill_of_ladings[0], query)

        return "I found some information but couldn't format it properly for voice. Please try again."

    def format_error_voice(self, error: str) -> str:
        """Format an error message for voice delivery."""
        # Keep errors brief and actionable
        if len(error) > 100:
            error = error[:97] + "..."

        return f"I encountered an issue: {error}. Please try again or ask for help."

    def format_help_voice(self) -> str:
        """Format help message for voice delivery."""
        return (
            "I can help you track containers and shipments. "
            "Say things like: 'Track container E F L U 7 8 9 6 5 4 3', "
            "'What's the status of B L A B C 1 2 3 4 5 6 7?', "
            "or 'Help me find my shipment'. "
            "What would you like to track?"
        )

    def format_status_update_voice(self, container: Container) -> str:
        """Format a status update for voice delivery."""
        status_text = self._get_voice_friendly_status(container.status)
        location_info = self._get_voice_friendly_location(container)

        response = f"Container {self._spell_container_id(container.containerNumber)} "

        if container.status == ContainerStatus.IN_TRANSIT:
            response += f"is currently {status_text}"
            if location_info:
                response += f" to {location_info}"
        elif container.status == ContainerStatus.AT_TERMINAL:
            response += f"is {status_text} at {location_info}"
        else:
            response += f"is {status_text} at {location_info}"

        # Add next step if available
        if container.nextStep:
            response += f". Next step: {container.nextStep}"

        return response

    def format_milestone_voice(self, container: Container, milestones: List[Dict]) -> str:
        """Format milestone information for voice delivery."""
        if not milestones:
            return f"No recent milestones for container {self._spell_container_id(container.containerNumber)}"

        latest_milestone = milestones[0]
        response = f"Latest update for container {self._spell_container_id(container.containerNumber)}: "

        event_type = latest_milestone.get('eventType', 'Status update').replace('_', ' ').lower()
        location = latest_milestone.get('location', 'Unknown location')
        timestamp = latest_milestone.get('timestamp', 'Unknown time')

        # Format timestamp for voice
        voice_timestamp = self._format_timestamp_voice(timestamp)

        response += f"{event_type} at {location} {voice_timestamp}"

        if len(milestones) > 1:
            response += f". That's the most recent of {len(milestones)} updates."

        return response

    def format_bl_summary_voice(self, bl: BillOfLading) -> str:
        """Format bill of lading summary for voice delivery."""
        container_count = len(bl.containers) if hasattr(bl, 'containers') else 0

        response = f"Bill of Lading {self._spell_bl_id(bl.blNumber)} shows {container_count} containers"

        if bl.origin and bl.destination:
            response += f" from {bl.origin} to {bl.destination}"

        if bl.estimatedArrival:
            arrival_text = self._format_timestamp_voice(bl.estimatedArrival)
            response += f", estimated arrival {arrival_text}"

        return response

    def _format_containers_voice(self, containers: List[Container], original_query: str) -> str:
        """Format multiple containers for voice delivery."""
        if len(containers) == 1:
            return self.format_status_update_voice(containers[0])
        elif len(containers) <= 3:
            # List multiple containers
            container_summaries = []
            for container in containers:
                status_text = self._get_voice_friendly_status(container.status)
                container_summaries.append(f"{self._spell_container_id(container.containerNumber)} is {status_text}")

            response = "I found multiple containers: "
            response += ", ".join(container_summaries)

            if containers and containers[0].nextStep:
                response += f". Next step for the first container: {containers[0].nextStep}"

            return response
        else:
            # Too many containers, summarize
            return f"I found {len(containers)} containers matching your query. The first container, {self._spell_container_id(containers[0].containerNumber)}, is {self._get_voice_friendly_status(containers[0].status)}. Would you like details on all of them?"

    def _format_bill_of_lading_voice(self, bl: BillOfLading, original_query: str) -> str:
        """Format bill of lading information for voice delivery."""
        return self.format_bl_summary_voice(bl)

    def _format_no_results_voice(self, query: str) -> str:
        """Format no results message for voice delivery."""
        return f"I couldn't find any containers or shipments matching '{query}'. Please check the number and try again, or ask for help."

    def _get_voice_friendly_status(self, status: ContainerStatus) -> str:
        """Get voice-friendly status description."""
        status_mapping = {
            ContainerStatus.IN_TRANSIT: "in transit",
            ContainerStatus.AT_TERMINAL: "at the terminal",
            ContainerStatus.DISCHARGED: "discharged from the vessel",
            ContainerStatus.CLEARED_FOR_EXAM: "cleared for customs examination",
            ContainerStatus.UNDER_EXAM: "under customs examination",
            ContainerStatus.RELEASED: "released and ready for pickup",
            ContainerStatus.DELIVERED: "delivered to destination"
        }

        return status_mapping.get(status, status.value.replace('_', ' ').lower())

    def _get_voice_friendly_location(self, container: Container) -> str:
        """Get voice-friendly location description."""
        if isinstance(container.location, dict):
            name = container.location.get('name', '')
            terminal = container.location.get('terminalId', '')
            if name and terminal:
                return f"{name}, {terminal}"
            elif name:
                return name
            elif terminal:
                return f"terminal {terminal}"
            else:
                return "an unknown location"
        else:
            return str(container.location) if container.location else "an unknown location"

    def _spell_container_id(self, container_id: str) -> str:
        """Spell out container ID for better voice clarity."""
        # Insert spaces for better pronunciation
        spelled = container_id.replace('EFLU', 'E F L U ').strip()
        return spelled

    def _spell_bl_id(self, bl_id: str) -> str:
        """Spell out BL ID for better voice clarity."""
        # Insert spaces for better pronunciation
        spelled = bl_id.replace('ABC', 'A B C ').strip()
        return spelled

    def _format_timestamp_voice(self, timestamp) -> str:
        """Format timestamp for voice delivery."""
        if isinstance(timestamp, datetime):
            # For recent dates, use relative time
            now = datetime.utcnow()
            diff = now - timestamp.replace(tzinfo=None)

            if diff.days == 0:
                hours = diff.seconds // 3600
                if hours == 0:
                    minutes = diff.seconds // 60
                    if minutes == 0:
                        return "just now"
                    elif minutes == 1:
                        return "one minute ago"
                    else:
                        return f"{minutes} minutes ago"
                elif hours == 1:
                    return "one hour ago"
                else:
                    return f"{hours} hours ago"
            elif diff.days == 1:
                return "yesterday"
            elif diff.days < 7:
                return f"{diff.days} days ago"
            else:
                return timestamp.strftime("on %B %d")
        else:
            return str(timestamp)

    def add_emphasis_breaks(self, text: str) -> str:
        """Add emphasis and breaks for better voice delivery."""
        # Add pauses after sentences
        text = re.sub(r'([.!?])', r'\1 <break time="300ms"/>', text)

        # Add shorter pauses after commas
        text = re.sub(r'(,)', r'\1 <break time="150ms"/>', text)

        # Emphasize important numbers and IDs
        text = re.sub(r'(\b[A-Z]{4}\d{7}\b)', r'<emphasis level="strong">\1</emphasis>', text)  # Container IDs
        text = re.sub(r'(\b[A-Z]{3}\d{7}\b)', r'<emphasis level="strong">\1</emphasis>', text)  # BL IDs

        return text

    def truncate_for_voice(self, text: str, max_chars: int = 500) -> str:
        """Truncate text for voice responses to avoid exceeding time limits."""
        if len(text) <= max_chars:
            return text

        # Try to truncate at sentence boundary
        truncated = text[:max_chars]
        sentences = re.split(r'([.!?])', truncated)

        # Find the last complete sentence
        for i in range(len(sentences) - 1, 0, -2):  # Go backwards through sentences
            if i > 0 and sentences[i] in '.!?':
                # Found a sentence end
                sentence_end = sum(len(sentences[j]) for j in range(i + 1))
                if sentence_end <= max_chars * 0.8:  # Keep at least 80% if it's a complete sentence
                    return ''.join(sentences[:i + 1])

        # If no sentence boundary found, truncate with ellipsis
        return truncated[:max_chars - 3] + "..."

    def enhance_pronunciation(self, text: str) -> str:
        """Enhance text for better pronunciation."""
        # Add phoneme hints for logistics terms
        enhancements = {
            "EFLU": '<phoneme alphabet="ipa" ph="ˌiːɛfɛlˈjuː">EFLU</phoneme>',
            "terminal": '<phoneme alphabet="ipa" ph="ˈtɜːrmɪnəl">terminal</phoneme>',
            "container": '<phoneme alphabet="ipa" ph="kənˈteɪnər">container</phoneme>',
            "milestone": '<phoneme alphabet="ipa" ph="ˈmaɪlstəʊn">milestone</phoneme>',
            "clearance": '<phoneme alphabet="ipa" ph="ˈklɪərəns">clearance</phoneme>',
            "customs": '<phoneme alphabet="ipa" ph="ˈkʌstəmz">customs</phoneme>',
            "examination": '<phoneme alphabet="ipa" ph="ɪɡˌzæmɪˈneɪʃən">examination</phoneme>',
        }

        enhanced = text
        for term, phoneme in enhancements.items():
            enhanced = enhanced.replace(term, phoneme)

        return enhanced

    def format_conversation_flow(self, messages: List[Message]) -> str:
        """Format conversation flow for voice delivery."""
        if not messages:
            return "No conversation history available."

        # Take last 3 exchanges (6 messages)
        recent_messages = messages[-6:]

        # Format as a conversation summary
        summary_parts = []
        for i, message in enumerate(recent_messages):
            if message.type == "user":
                summary_parts.append(f"You asked: {message.content}")
            else:
                summary_parts.append(f"I said: {message.content}")

        return " | ".join(summary_parts)


# Global instance
_voice_formatter: Optional[VoiceResponseFormatter] = None


async def get_voice_formatter() -> VoiceResponseFormatter:
    """Get or create voice response formatter instance."""
    global _voice_formatter
    if _voice_formatter is None:
        _voice_formatter = await VoiceResponseFormatter().get_instance()
    return _voice_formatter
