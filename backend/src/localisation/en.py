"""
English Language Pack for EFL Agent Assistant
Logistics terminology and culturally appropriate messages for West African English context.
"""

from typing import Dict, Any
from enum import Enum


class ContainerStatus(str, Enum):
    """Container status descriptions in West African English."""
    IN_TRANSIT = "in_transit"
    AT_TERMINAL = "at_terminal"
    CLEARED_FOR_EXAM = "cleared_for_exam"
    UNDER_EXAMINATION = "under_examination"
    RELEASED = "released"
    ON_HOLD = "on_hold"
    DELIVERED = "delivered"


class LogisticsTerminology:
    """Core logistics terminology for EFL operations."""

    # Container and shipment identifiers
    CONTAINER_ID = "container_id"
    BILL_OF_LADING = "bill_of_lading"
    BL_NUMBER = "bl_number"
    SHIPMENT_REFERENCE = "shipment_reference"

    # Status and location terms
    STATUS = "status"
    LOCATION = "location"
    DESTINATION = "destination"
    CURRENT_POSITION = "current_position"

    # Time and scheduling terms
    ESTIMATED_TIME_ARRIVAL = "estimated_time_arrival"
    ACTUAL_TIME_ARRIVAL = "actual_time_arrival"
    ESTIMATED_TIME_DEPARTURE = "estimated_time_departure"
    VESSEL_ARRIVAL = "vessel_arrival"

    # Terminal operations
    TERMINAL = "terminal"
    YARD = "yard"
    GATE = "gate"
    STACK = "stack"

    # Documentation and customs
    CUSTOMS_EXAMINATION = "customs_examination"
    CLEARANCE = "clearance"
    DOCUMENTATION = "documentation"
    RELEASE_ORDER = "release_order"


class EnglishLanguagePack:
    """English language pack with logistics-specific terminology."""

    def __init__(self):
        self.terminology = LogisticsTerminology()

    # Common logistics terms translations
    LOGISTICS_TERMS = {
        "container": "container",
        "bill_of_lading": "bill of lading",
        "bl_number": "BL number",
        "shipment": "shipment",
        "consignment": "consignment",
        "cargo": "cargo",
        "freight": "freight",
        "vessel": "ship",
        "voyage": "voyage",
        "terminal": "terminal yard",
        "depot": "container depot",
        "yard": "storage yard",
        "stack": "container stack",
        "bay": "bay",
        "berth": "berth",
        "discharge": "offload",
        "loading": "loading",
        "transshipment": "transshipment",
        "transit": "in transit",
        "clearance": "customs clearance",
        "examination": "customs examination",
        "inspection": "inspection",
        "release": "release",
        "hold": "on hold",
        "detention": "detention",
        "demurrage": "demurrage charges",
        "storage": "storage charges",
        "documentation": "shipping documents",
        "manifest": "cargo manifest",
        "waybill": "waybill",
        "invoice": "commercial invoice",
        "packing_list": "packing list",
        "certificate": "certificate",
        "permit": "permit",
        "license": "license",
    }

    # Status descriptions
    STATUS_DESCRIPTIONS = {
        ContainerStatus.IN_TRANSIT: "The container is currently in transit and moving towards the terminal",
        ContainerStatus.AT_TERMINAL: "The container has arrived at the terminal and is in the yard",
        ContainerStatus.CLEARED_FOR_EXAM: "The container has been cleared by customs and is ready for examination booking",
        ContainerStatus.UNDER_EXAMINATION: "The container is currently undergoing customs examination",
        ContainerStatus.RELEASED: "The container has been released and is ready for pickup",
        ContainerStatus.ON_HOLD: "The container is on hold pending documentation or payment",
        ContainerStatus.DELIVERED: "The container has been delivered to the consignee",
    }

    # Location descriptions
    LOCATION_DESCRIPTIONS = {
        "efl_terminal_ikorodu": "EFL Terminal, Ikorodu, Lagos State",
        "lagos_port_complex": "Lagos Port Complex, Apapa",
        "tin_can_port": "Tin Can Island Port, Apapa",
        "lekki_deep_seaport": "Lekki Deep Seaport",
        "on_vessel": "aboard the vessel",
        "in_transit": "in transit between ports",
        "at_transshipment_port": "at transshipment port",
        "at_destination": "at final destination",
    }

    # Next step recommendations
    NEXT_STEP_MESSAGES = {
        ContainerStatus.IN_TRANSIT: "The container is expected to arrive at the terminal soon. Please check back later for updates.",
        ContainerStatus.AT_TERMINAL: "The container is at the terminal. You can now proceed with customs clearance procedures.",
        ContainerStatus.CLEARED_FOR_EXAM: "You may now book a customs examination appointment through the terminal system.",
        ContainerStatus.UNDER_EXAMINATION: "The container is being examined. Please wait for examination results before proceeding.",
        ContainerStatus.RELEASED: "The container is ready for pickup. Please arrange collection with the terminal.",
        ContainerStatus.ON_HOLD: "Please resolve the documentation or payment issues to release the hold on this container.",
        ContainerStatus.DELIVERED: "The container has been delivered. No further action is required.",
    }

    # Voice-specific prompts
    VOICE_PROMPTS = {
        "welcome": "Welcome to EFL Agent Assistant. How can I help you today?",
        "container_confirmation": "I heard you say container {container_id}. Is that correct?",
        "bl_confirmation": "I heard you say BL number {bl_number}. Is that correct?",
        "status_request": "What would you like to know about this {item_type}?",
        "next_step_request": "Would you like to hear what to do next?",
        "clarification_needed": "I didn't catch that clearly. Could you please repeat?",
        "timeout_warning": "Are you still there? The line will disconnect in 30 seconds if there's no response.",
        "goodbye": "Thank you for using EFL Agent Assistant. Have a great day!",
    }

    # Error messages
    ERROR_MESSAGES = {
        "container_not_found": "I'm sorry, I couldn't find any record for container {container_id}. Please check the number and try again.",
        "bl_not_found": "I'm sorry, I couldn't find any record for BL number {bl_number}. Please check the number and try again.",
        "multiple_containers": "I found {count} containers under that BL number. Which specific container would you like to track?",
        "system_unavailable": "I'm currently unable to retrieve that information. Please try again in a few moments or contact our customer service team.",
        "permission_denied": "I'm sorry, you don't have permission to access information for that container. Please contact your administrator.",
        "invalid_format": "The {field_name} format appears to be incorrect. Please check and try again.",
        "network_error": "I'm experiencing some connection issues. Let me try again...",
    }

    # Success confirmations
    SUCCESS_MESSAGES = {
        "information_retrieved": "I've retrieved the information for {item_type} {identifier}.",
        "status_updated": "The status has been updated successfully.",
        "request_processed": "Your request has been processed. You should receive a confirmation shortly.",
    }

    # Help and guidance
    HELP_MESSAGES = {
        "general_help": "I can help you track containers, check bill of lading status, or provide information about terminal operations. What would you like to know?",
        "container_help": "You can ask me about container status by saying the container number, like 'Track container EFLU7896543'.",
        "bl_help": "You can ask about shipments by saying the BL number, like 'Track BL ABC1234567'.",
        "status_help": "I can tell you the current status, location, next steps, or recent milestones for your containers.",
    }

    def get_logistics_term(self, term_key: str) -> str:
        """Get translated logistics terminology."""
        return self.LOGISTICS_TERMS.get(term_key, term_key.replace("_", " ").title())

    def get_status_description(self, status: ContainerStatus) -> str:
        """Get culturally appropriate status description."""
        return self.STATUS_DESCRIPTIONS.get(status, f"Status: {status.replace('_', ' ')}")

    def get_location_description(self, location_code: str) -> str:
        """Get location description with local context."""
        return self.LOCATION_DESCRIPTIONS.get(location_code, location_code.replace("_", " ").title())

    def get_next_step_message(self, status: ContainerStatus) -> str:
        """Get contextually appropriate next step guidance."""
        return self.NEXT_STEP_MESSAGES.get(status, "Please check with the terminal for the next steps.")

    def get_voice_prompt(self, prompt_type: str, **kwargs) -> str:
        """Get voice-specific prompt with variable substitution."""
        template = self.VOICE_PROMPTS.get(prompt_type, "")
        return template.format(**kwargs) if kwargs else template

    def get_error_message(self, error_type: str, **kwargs) -> str:
        """Get culturally appropriate error message."""
        template = self.ERROR_MESSAGES.get(error_type, "An error occurred while processing your request.")
        return template.format(**kwargs) if kwargs else template

    def get_success_message(self, message_type: str, **kwargs) -> str:
        """Get success confirmation message."""
        template = self.SUCCESS_MESSAGES.get(message_type, "Your request was processed successfully.")
        return template.format(**kwargs) if kwargs else template

    def get_help_message(self, help_type: str) -> str:
        """Get contextual help message."""
        return self.HELP_MESSAGES.get(help_type, self.HELP_MESSAGES["general_help"])

    def format_container_status_response(self, container_id: str, status: ContainerStatus,
                                       location: str = None, next_step: str = None) -> Dict[str, str]:
        """Format a complete container status response."""
        return {
            "status_description": self.get_status_description(status),
            "location": self.get_location_description(location) if location else "Location not specified",
            "next_step": next_step or self.get_next_step_message(status),
            "voice_summary": self._create_voice_summary(container_id, status, location)
        }

    def _create_voice_summary(self, container_id: str, status: ContainerStatus, location: str) -> str:
        """Create a concise voice-friendly summary."""
        status_text = status.replace("_", " ")
        location_text = self.get_location_description(location) if location else "unknown location"

        return f"Container {container_id} is currently {status_text} at {location_text}."

    def format_bl_status_response(self, bl_number: str, containers: list, status: str = None) -> Dict[str, Any]:
        """Format a complete BL status response."""
        container_list = ", ".join(containers) if containers else "No containers found"

        return {
            "bl_summary": f"BL {bl_number} contains the following containers: {container_list}",
            "status": status or "Status information not available",
            "voice_summary": self._create_bl_voice_summary(bl_number, containers)
        }

    def _create_bl_voice_summary(self, bl_number: str, containers: list) -> str:
        """Create a concise voice-friendly BL summary."""
        if not containers:
            return f"BL number {bl_number} has no containers associated with it."

        if len(containers) == 1:
            return f"BL {bl_number} corresponds to container {containers[0]}."

        container_text = ", ".join(containers[:-1]) + f" and {containers[-1]}"
        return f"BL {bl_number} corresponds to containers {container_text}."


# Singleton instance for easy import
english_pack = EnglishLanguagePack()
