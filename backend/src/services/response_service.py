"""ResponseService for natural language response formatting."""

from typing import Dict, List, Any, Optional
from datetime import datetime

from src.models.container import Container, BillOfLading, ContainerStatus
from src.models.agent import ChannelType
from src.services.track_service import TrackService


class ResponseService:
    """Service for formatting natural language responses."""

    def __init__(self):
        self.track_service = None

    async def get_instance(self) -> "ResponseService":
        """Get singleton instance with dependencies initialized."""
        if self.track_service is None:
            self.track_service = await TrackService().get_instance()
        return self

    def format_tracking_response(
        self,
        query: str,
        containers: List[Container],
        bill_of_ladings: List[BillOfLading],
        channel: ChannelType
    ) -> str:
        """Format a comprehensive tracking response."""
        if not containers and not bill_of_ladings:
            return self._format_no_results_response(query)

        if containers:
            return self._format_container_response(containers[0], channel)

        if bill_of_ladings:
            return self._format_bl_response(bill_of_ladings[0], channel)

        return "I found some information but couldn't format it properly. Please try again."

    def format_error_response(self, error: str, channel: ChannelType) -> str:
        """Format an error response."""
        if channel == ChannelType.VOICE:
            return f"I encountered an issue: {error}. Please try again."
        else:
            return f"Error: {error}. Please check your input and try again."

    def format_help_response(self, channel: ChannelType) -> str:
        """Format a help response."""
        if channel == ChannelType.VOICE:
            return "I can help you track containers and shipments. Just say the container number or bill of lading number. For example, 'Track container EFLU7896543' or 'What's the status of BL ABC1234567?'"

        return """I can help you track containers and shipments. Here are some examples:

**Container Tracking:**
• "Track container EFLU7896543"
• "What's the status of container EFLU7896543?"
• "Show me container EFLU7896543 milestones"

**Bill of Lading Tracking:**
• "Track BL ABC1234567"
• "What's the status of shipment ABC1234567?"

**Multi-container queries:**
• "Track containers EFLU7896543 and EFLU7896544"
• "Show me all containers for BL ABC1234567"

I can also help with vessel information, schedules, and general logistics inquiries."""

    def _format_container_response(self, container: Container, channel: ChannelType) -> str:
        """Format response for container tracking."""
        status_text = self._format_status_text(container.status)
        location_text = self._format_location_text(container.location)

        # Determine response style based on channel
        if channel == ChannelType.VOICE:
            response = f"Container {container.containerNumber} is currently {status_text} at {location_text}."
        else:
            response = f"**Container: {container.containerNumber}**\n\n"
            response += f"**Status:** {status_text}\n"
            response += f"**Location:** {location_text}\n"

        # Add additional details for chat
        if channel == ChannelType.CHAT:
            response += f"\n**Container Details:**\n"
            response += f"• ISO Code: {container.isoCode}\n"
            response += f"• Bill of Lading: {container.billOfLading.blNumber}\n"
            response += f"• Shipping Line: {container.billOfLading.shippingLine}\n"
            response += f"• Last Updated: {container.lastUpdated.strftime('%Y-%m-%d %H:%M UTC')}\n"

        # Add next step
        if container.nextStep:
            response += f"\n**Next Step:** {container.nextStep}"

        return response

    def _format_bl_response(self, bl: BillOfLading, channel: ChannelType) -> str:
        """Format response for bill of lading tracking."""
        if channel == ChannelType.VOICE:
            response = f"Bill of Lading {bl.blNumber} shows {len(bl.containers) if hasattr(bl, 'containers') else 0} containers."
            response += f" The shipment is from {bl.origin} to {bl.destination}"
            if bl.estimatedArrival:
                response += f", with estimated arrival on {bl.estimatedArrival.strftime('%B %d, %Y')}."
        else:
            response = f"**Bill of Lading: {bl.blNumber}**\n\n"
            response += f"**Route:** {bl.origin} → {bl.destination}\n"
            response += f"**Vessel:** {bl.vesselVoyage.vesselName}\n"
            response += f"**Voyage:** {bl.vesselVoyage.voyageNumber}\n"
            response += f"**Shipping Line:** {bl.shippingLine}\n"

            if bl.estimatedArrival:
                response += f"**Estimated Arrival:** {bl.estimatedArrival.strftime('%Y-%m-%d %H:%M UTC')}\n"

            if hasattr(bl, 'containers') and bl.containers:
                response += f"**Containers:** {len(bl.containers)} containers in this shipment\n"

        return response

    def _format_no_results_response(self, query: str) -> str:
        """Format response when no results are found."""
        return f"I couldn't find any containers or shipments matching '{query}'. Please check the container number or bill of lading number and try again."

    def _format_status_text(self, status: ContainerStatus) -> str:
        """Format container status as human-readable text."""
        status_mapping = {
            ContainerStatus.IN_TRANSIT: "in transit",
            ContainerStatus.AT_TERMINAL: "at the terminal",
            ContainerStatus.DISCHARGED: "discharged from the vessel",
            ContainerStatus.CLEARED_FOR_EXAM: "cleared for customs examination",
            ContainerStatus.UNDER_EXAM: "under customs examination",
            ContainerStatus.RELEASED: "released and ready for pickup",
            ContainerStatus.DELIVERED: "delivered"
        }

        return status_mapping.get(status, status.value.replace('_', ' '))

    def _format_location_text(self, location: Dict) -> str:
        """Format location information as human-readable text."""
        if isinstance(location, dict):
            name = location.get('name', 'Unknown Location')
            terminal = location.get('terminalId', 'Unknown Terminal')
            return f"{name}, {terminal}"
        else:
            return str(location)

    def format_container_list_response(self, containers: List[Container], channel: ChannelType) -> str:
        """Format response for multiple containers."""
        if not containers:
            return "No containers found."

        if len(containers) == 1:
            return self._format_container_response(containers[0], channel)

        if channel == ChannelType.VOICE:
            response = f"Found {len(containers)} containers. "
            response += ", ".join([f"{c.containerNumber} is {self._format_status_text(c.status)}" for c in containers[:3]])
            if len(containers) > 3:
                response += f", and {len(containers) - 3} more."
        else:
            response = f"**Found {len(containers)} containers:**\n\n"
            for i, container in enumerate(containers[:5], 1):
                response += f"{i}. **{container.containerNumber}** - {self._format_status_text(container.status)}\n"
                response += f"   Location: {self._format_location_text(container.location)}\n"
                response += f"   BL: {container.billOfLading.blNumber}\n\n"

            if len(containers) > 5:
                response += f"... and {len(containers) - 5} more containers."

        return response

    def format_milestone_response(self, container: Container, milestones: List[Dict], channel: ChannelType) -> str:
        """Format milestone history response."""
        if not milestones:
            return f"No milestone history available for container {container.containerNumber}."

        if channel == ChannelType.VOICE:
            response = f"Here are the recent milestones for container {container.containerNumber}: "
            for milestone in milestones[:3]:
                response += f"{milestone.get('eventType', 'Unknown')} at {milestone.get('location', 'Unknown location')}, "
            response += "and so on."
        else:
            response = f"**Milestone History for {container.containerNumber}:**\n\n"
            for i, milestone in enumerate(milestones[:10], 1):
                timestamp = milestone.get('timestamp', 'Unknown time')
                event_type = milestone.get('eventType', 'Unknown event').replace('_', ' ').title()
                location = milestone.get('location', 'Unknown location')
                description = milestone.get('description', '')

                response += f"{i}. **{event_type}** - {timestamp}\n"
                response += f"   Location: {location}\n"
                if description:
                    response += f"   {description}\n"
                response += "\n"

            if len(milestones) > 10:
                response += f"... and {len(milestones) - 10} more milestones."

        return response

    def format_cultural_response(self, text: str, locale: str = "en_NG") -> str:
        """Format response for cultural appropriateness."""
        # In a real implementation, this would apply cultural formatting
        # For now, just return the text as-is
        return text

    def truncate_for_voice(self, text: str, max_chars: int = 500) -> str:
        """Truncate text for voice responses to avoid exceeding time limits."""
        if len(text) <= max_chars:
            return text

        # Try to truncate at a sentence boundary
        truncated = text[:max_chars]
        last_period = truncated.rfind('.')
        last_exclamation = truncated.rfind('!')
        last_question = truncated.rfind('?')

        # Find the latest sentence ender
        sentence_end = max(last_period, last_exclamation, last_question)

        if sentence_end > max_chars * 0.7:  # If we can keep at least 70% with a sentence
            return truncated[:sentence_end + 1]
        else:
            return truncated + "..."

    def enhance_for_voice(self, text: str) -> str:
        """Enhance text for better voice delivery."""
        # Add pauses for better speech flow
        enhanced = text.replace('.', '. <break time="300ms"/>')
        enhanced = enhanced.replace('?', '? <break time="400ms"/>')
        enhanced = enhanced.replace('!', '! <break time="200ms"/>')
        enhanced = enhanced.replace(',', ', <break time="100ms"/>')

        return enhanced
