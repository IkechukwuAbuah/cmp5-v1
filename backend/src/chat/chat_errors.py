"""Chat-specific error handling and user feedback utilities."""

from __future__ import annotations

import logging
from typing import Dict, Optional


logger = logging.getLogger(__name__)


class ChatErrorManager:
    """Provide consistent error responses for chat interactions."""

    _ERROR_MESSAGES: Dict[str, str] = {
        "UNKNOWN_ERROR": "Sorry, something went wrong while processing your request.",
        "NOT_AUTHORIZED": "You do not have permission to access that information.",
        "NOT_FOUND": "I could not find anything that matches that request.",
        "RATE_LIMIT": "Too many requests in a short period. Please wait a moment and try again.",
        "UPSTREAM_UNAVAILABLE": "Upstream tracking providers are unavailable right now. I will keep trying in the background.",
        "SESSION_EXPIRED": "This chat session has expired due to inactivity. Let's start a new one.",
    }

    _RECOVERY_ACTIONS: Dict[str, str] = {
        "UNKNOWN_ERROR": "Try rephrasing the request or provide a specific container or BL number.",
        "NOT_AUTHORIZED": "Please contact your supervisor if you believe you should have access.",
        "NOT_FOUND": "Check the container or BL number and try again. I can also help search by voyage.",
        "RATE_LIMIT": "Hold on for a few seconds before sending another message.",
        "UPSTREAM_UNAVAILABLE": "I'll notify you as soon as I have fresh data. Meanwhile, I can show cached information.",
        "SESSION_EXPIRED": "Send your request again and I'll continue from there.",
    }

    _USER_HINTS: Dict[str, str] = {
        "query_missing": "Include a container ID like `EFLU7896543` or a BL number such as `ABC1234567`.",
        "multi_channel": "You can switch to voice at any time—I'll keep your chat history synced.",
    }

    @classmethod
    def build_error_payload(
        cls,
        code: str,
        correlation_id: Optional[str] = None,
        details: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Optional[str]]:
        """Return a structured error payload suitable for chat responses."""

        normalized_code = code if code in cls._ERROR_MESSAGES else "UNKNOWN_ERROR"
        message = cls._ERROR_MESSAGES[normalized_code]
        recovery = cls._RECOVERY_ACTIONS.get(normalized_code, cls._RECOVERY_ACTIONS["UNKNOWN_ERROR"])

        payload: Dict[str, Optional[str]] = {
            "code": normalized_code,
            "message": message,
            "recovery": recovery,
            "correlationId": correlation_id,
        }

        if details:
            payload["details"] = " | ".join(f"{key}: {value}" for key, value in details.items())

        return payload

    @classmethod
    def get_hint(cls, hint_key: str) -> Optional[str]:
        """Return a user-facing hint by key."""

        hint = cls._USER_HINTS.get(hint_key)
        if hint is None:
            logger.debug("Requested unknown chat hint: %s", hint_key)
        return hint


__all__ = ["ChatErrorManager"]

