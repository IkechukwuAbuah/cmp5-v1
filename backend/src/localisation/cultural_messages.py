"""
Culturally Appropriate Error Messages for EFL Logistics Domain
Provides culturally sensitive, contextually appropriate error messages
tailored for West African English speakers in the logistics and shipping industry.
"""

import logging
from typing import Dict, List, Optional, Tuple
from enum import Enum
from dataclasses import dataclass

logger = logging.getLogger(__name__)


class ErrorContext(str, Enum):
    """Context categories for different types of errors."""
    CONTAINER_NOT_FOUND = "container_not_found"
    BL_NOT_FOUND = "bl_not_found"
    PERMISSION_DENIED = "permission_denied"
    SYSTEM_UNAVAILABLE = "system_unavailable"
    NETWORK_ERROR = "network_error"
    INVALID_INPUT = "invalid_input"
    MULTIPLE_MATCHES = "multiple_matches"
    TIMEOUT = "timeout"
    DATA_STALENESS = "data_staleness"


class CulturalTone(str, Enum):
    """Cultural tone variations for different communication styles."""
    FORMAL = "formal"
    RESPECTFUL = "respectful"
    FRIENDLY = "friendly"
    APOLOGETIC = "apologetic"
    HELPFUL = "helpful"
    PROFESSIONAL = "professional"


@dataclass
class CulturalErrorMessage:
    """Structured culturally appropriate error message."""
    message: str
    alternatives: List[str]
    next_steps: List[str]
    tone: CulturalTone
    requires_confirmation: bool = False


class CulturalMessageHandler:
    """Handles culturally appropriate error messages for the logistics domain."""

    def __init__(self):
        self.error_templates = self._initialize_error_templates()
        self.cultural_contexts = self._initialize_cultural_contexts()

    def _initialize_error_templates(self) -> Dict[ErrorContext, CulturalErrorMessage]:
        """Initialize culturally appropriate error message templates."""
        return {
            ErrorContext.CONTAINER_NOT_FOUND: CulturalErrorMessage(
                message="I'm sorry, I couldn't find any record for container {container_id}. Please double-check the container number and try again.",
                alternatives=[
                    "E kaasan, container {container_id} ko si ni system wa. Jọwọ ẹ tun ka number na.",
                    "No wahala, but I no see container {container_id} for our records. Make you check the number again.",
                    "Please sir/ma, I cannot locate container {container_id} in our terminal system. Kindly verify the identification number."
                ],
                next_steps=[
                    "Please confirm the container number is correct",
                    "Check if it's an EFL container (starts with EFLU)",
                    "Contact terminal operations for assistance",
                    "Try searching by Bill of Lading number instead"
                ],
                tone=CulturalTone.HELPFUL,
                requires_confirmation=True
            ),

            ErrorContext.BL_NOT_FOUND: CulturalErrorMessage(
                message="I apologize, but I couldn't find any shipment record for BL number {bl_number}. Please verify the Bill of Lading number.",
                alternatives=[
                    "E jọwọ, BL number {bl_number} ko si ni system wa. Ẹ tun ka number na.",
                    "Sorry o, I no see that BL number {bl_number} for our records. Make you check am well.",
                    "Please sir/ma, the Bill of Lading number {bl_number} is not found in our system. Kindly confirm the reference number."
                ],
                next_steps=[
                    "Verify the BL number format is correct",
                    "Check if it's a CMA CGM or EFL terminal BL",
                    "Try searching by container number instead",
                    "Contact documentation department for assistance"
                ],
                tone=CulturalTone.APOLOGETIC,
                requires_confirmation=True
            ),

            ErrorContext.PERMISSION_DENIED: CulturalErrorMessage(
                message="I'm sorry, but you don't have access permission for this container information. Please contact your administrator or the cargo owner.",
                alternatives=[
                    "E kaasan, o ko ni ẹtọ lati riran information yi. Jọwọ ẹ kan administrator tabi owner cargo na.",
                    "No wahala, but you no get permission to see this container details. Make you contact your supervisor.",
                    "Please sir/ma, access to this container information is restricted. Kindly contact the authorized personnel or system administrator."
                ],
                next_steps=[
                    "Contact your company's clearing agent coordinator",
                    "Speak with the cargo owner or consignee",
                    "Reach out to EFL terminal customer service",
                    "Check if you have the correct access credentials"
                ],
                tone=CulturalTone.RESPECTFUL,
                requires_confirmation=False
            ),

            ErrorContext.SYSTEM_UNAVAILABLE: CulturalErrorMessage(
                message="I apologize for the inconvenience, but our system is currently experiencing technical difficulties. Please try again in a few minutes.",
                alternatives=[
                    "E kaasan fun inconvenience yi, system wa n ni technical issues bayi. Jọwọ ẹ tun gbiyanju ni isẹju diẹ.",
                    "Sorry for the wahala, our system dey face some technical problems now. Make you try again later.",
                    "Please accept our apologies sir/ma, we are experiencing temporary system challenges. Kindly attempt your request again shortly."
                ],
                next_steps=[
                    "Wait 2-3 minutes and try again",
                    "Contact EFL terminal helpdesk if issue persists",
                    "Use alternative communication channels if available",
                    "Check our website for system status updates"
                ],
                tone=CulturalTone.APOLOGETIC,
                requires_confirmation=False
            ),

            ErrorContext.NETWORK_ERROR: CulturalErrorMessage(
                message="I'm experiencing some connection issues while retrieving your information. Let me try again...",
                alternatives=[
                    "Mo n ni connection issues nigba ti mo n gbe information yin wa. Jẹ ki n tun gbiyanju...",
                    "Network dey give us small problem now. Make I try again for you.",
                    "We are encountering connectivity challenges at the moment. Please allow me to retry your request."
                ],
                next_steps=[
                    "The system will automatically retry the request",
                    "Wait a moment for automatic retry",
                    "Contact support if the issue continues",
                    "Try using a different device or network if possible"
                ],
                tone=CulturalTone.HELPFUL,
                requires_confirmation=False
            ),

            ErrorContext.INVALID_INPUT: CulturalErrorMessage(
                message="I notice there might be an issue with the format of {field_name}. Please check and try again.",
                alternatives=[
                    "Mo riran pe o le ni issue pẹlu format {field_name}. Jọwọ ẹ tun ka.",
                    "The {field_name} format no dey correct. Make you check am well.",
                    "Please sir/ma, there appears to be a formatting issue with the {field_name}. Kindly review and try again."
                ],
                next_steps=[
                    "Verify the correct format for the field",
                    "Check examples of valid input formats",
                    "Contact support for format clarification",
                    "Use the help feature for format guidance"
                ],
                tone=CulturalTone.HELPFUL,
                requires_confirmation=True
            ),

            ErrorContext.MULTIPLE_MATCHES: CulturalErrorMessage(
                message="I found multiple containers that might match your search. Could you please specify which one you need information about?",
                alternatives=[
                    "Mo riran ọpọlọpọ container ti o le match search yin. Jọwọ ẹ specify ewo ni ẹ fẹ information nipa rẹ?",
                    "I see many containers wey fit your search. Make you tell me which one you want.",
                    "Several containers match your criteria sir/ma. Please specify which particular container you require information for."
                ],
                next_steps=[
                    "Provide the specific container number",
                    "Specify the Bill of Lading number",
                    "Indicate the cargo owner or consignee name",
                    "List the containers and ask for clarification"
                ],
                tone=CulturalTone.HELPFUL,
                requires_confirmation=True
            ),

            ErrorContext.TIMEOUT: CulturalErrorMessage(
                message="I'm taking longer than expected to retrieve your information. This might be due to high system activity. Please bear with me.",
                alternatives=[
                    "Mo n gba ju expected lo lati gba information yin. E le jẹ nitori high system activity. Jọwọ ẹ bear with me.",
                    "The system dey take longer than normal. E fit be because many people dey use am now. No wahala, I go get am.",
                    "Please be patient sir/ma, we are experiencing higher than usual system load. Your request will be processed shortly."
                ],
                next_steps=[
                    "Wait a bit longer for the response",
                    "Try again during less busy hours",
                    "Contact support if timeout persists",
                    "Use the callback feature if available"
                ],
                tone=CulturalTone.APOLOGETIC,
                requires_confirmation=False
            ),

            ErrorContext.DATA_STALENESS: CulturalErrorMessage(
                message="The information I'm showing might be a few minutes old. For the most current status, please check with terminal operations directly.",
                alternatives=[
                    "Information ti mo n fi han le ti old ni isẹju diẹ. Fun status to current jù, jọwọ ẹ check pẹlu terminal operations directly.",
                    "This data fit don old small. Make you confirm with terminal people for latest update.",
                    "Please note that this information may not be completely up-to-date. For the most recent status, kindly contact terminal operations directly."
                ],
                next_steps=[
                    "Call terminal operations for real-time update",
                    "Check the terminal website for live status",
                    "Visit the terminal if possible for immediate assistance",
                    "Wait a few minutes and try again"
                ],
                tone=CulturalTone.HELPFUL,
                requires_confirmation=False
            )
        }

    def _initialize_cultural_contexts(self) -> Dict[str, Dict[str, str]]:
        """Initialize cultural context patterns for different regions."""
        return {
            "nigerian": {
                "politeness_prefix": "Please sir/ma",
                "apology_style": "E kaasan / I'm sorry",
                "helpfulness": "No wahala / No problem",
                "confirmation_request": "Jọwọ / Please",
                "gratitude": "Thank you / Ese",
            },
            "west_african": {
                "politeness_prefix": "Please",
                "apology_style": "I apologize",
                "helpfulness": "Let me help you",
                "confirmation_request": "Could you please",
                "gratitude": "Thank you",
            },
            "formal_business": {
                "politeness_prefix": "Dear sir/madam",
                "apology_style": "We sincerely apologize",
                "helpfulness": "We would be happy to assist",
                "confirmation_request": "Kindly",
                "gratitude": "We appreciate your understanding",
            }
        }

    def get_cultural_error_message(
        self,
        error_context: ErrorContext,
        cultural_context: str = "nigerian",
        **kwargs
    ) -> Dict[str, str]:
        """
        Get culturally appropriate error message for the specified context.

        Args:
            error_context: The type of error that occurred
            cultural_context: Cultural context (nigerian, west_african, formal_business)
            **kwargs: Variables to substitute in the message template

        Returns:
            Dict containing message, alternatives, next_steps, and tone
        """
        if error_context not in self.error_templates:
            return self._get_default_error_message(cultural_context, **kwargs)

        template = self.error_templates[error_context]

        # Apply cultural context modifications
        message = self._apply_cultural_context(template.message, cultural_context)
        alternatives = [
            self._apply_cultural_context(alt, cultural_context)
            for alt in template.alternatives
        ]

        # Format message with variables
        try:
            formatted_message = message.format(**kwargs)
            formatted_alternatives = [
                alt.format(**kwargs) for alt in alternatives
            ]
        except KeyError as e:
            logger.warning(f"Missing format variable in error message: {e}")
            formatted_message = message
            formatted_alternatives = alternatives

        return {
            "primary_message": formatted_message,
            "alternative_messages": formatted_alternatives,
            "next_steps": template.next_steps,
            "tone": template.tone.value,
            "requires_confirmation": template.requires_confirmation,
            "cultural_context": cultural_context
        }

    def _apply_cultural_context(self, message: str, cultural_context: str) -> str:
        """Apply cultural context modifications to a message."""
        if cultural_context not in self.cultural_contexts:
            return message

        context = self.cultural_contexts[cultural_context]

        # Add cultural politeness prefix if not present
        if not message.startswith(tuple(context.values())):
            politeness_prefix = context.get("politeness_prefix", "")
            if politeness_prefix and politeness_prefix not in message:
                message = f"{politeness_prefix}, {message.lower()}"

        # Apply cultural apology style
        apology_style = context.get("apology_style", "I'm sorry")
        if "I'm sorry" in message and apology_style != "I'm sorry":
            message = message.replace("I'm sorry", apology_style)

        # Apply cultural helpfulness expressions
        helpfulness = context.get("helpfulness", "Let me help you")
        if helpfulness not in message and "help" in message.lower():
            # This is a simple replacement - more sophisticated logic could be added
            pass

        return message

    def _get_default_error_message(self, cultural_context: str = "nigerian", **kwargs) -> Dict[str, str]:
        """Get a default error message when specific context is not available."""
        context = self.cultural_contexts.get(cultural_context, self.cultural_contexts["nigerian"])

        default_message = f"{context['politeness_prefix']}, I'm experiencing an issue processing your request. {context['helpfulness']}."

        return {
            "primary_message": default_message,
            "alternative_messages": [
                f"{context['apology_style']}, there seems to be a technical issue. {context['helpfulness']}.",
                f"{context['politeness_prefix']}, our system is having some challenges right now. Please try again later."
            ],
            "next_steps": [
                "Please try your request again",
                "Contact customer support if the issue persists",
                "Check our website for system updates"
            ],
            "tone": CulturalTone.HELPFUL.value,
            "requires_confirmation": False,
            "cultural_context": cultural_context
        }

    def get_voice_optimized_message(self, error_context: ErrorContext,
                                  cultural_context: str = "nigerian") -> str:
        """
        Get a voice-optimized version of the error message (shorter, clearer for voice).

        Args:
            error_context: The type of error
            cultural_context: Cultural context preference

        Returns:
            Voice-optimized error message
        """
        message_data = self.get_cultural_error_message(error_context, cultural_context)

        # Create shorter voice-friendly version
        primary_msg = message_data["primary_message"]

        # Remove politeness prefixes for voice brevity
        context = self.cultural_contexts.get(cultural_context, self.cultural_contexts["nigerian"])
        politeness_prefix = context.get("politeness_prefix", "")

        if primary_msg.startswith(politeness_prefix):
            primary_msg = primary_msg.replace(f"{politeness_prefix}, ", "")

        # Limit length for voice (aim for 15-20 seconds max)
        if len(primary_msg) > 150:
            primary_msg = primary_msg[:147] + "..."

        return primary_msg

    def suggest_alternative_message(self, error_context: ErrorContext,
                                  user_feedback: Optional[str] = None) -> str:
        """
        Suggest an alternative message based on user feedback or context.

        Args:
            error_context: The original error context
            user_feedback: Optional user feedback about the message

        Returns:
            Alternative message suggestion
        """
        if error_context not in self.error_templates:
            return "I'm sorry, I couldn't find a better way to express that."

        template = self.error_templates[error_context]
        alternatives = template.alternatives

        if not alternatives:
            return template.message

        # Return a random alternative or the first one
        import random
        return random.choice(alternatives)


# Singleton instance for easy import
cultural_handler = CulturalMessageHandler()
