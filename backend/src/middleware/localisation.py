"""
Localisation Middleware for EFL Agent Assistant
Handles dynamic language switching, cultural context detection,
and provides localisation services throughout the request lifecycle.
"""

import logging
from typing import Dict, Optional, List, Tuple
from contextlib import contextmanager
from contextvars import ContextVar
from time import perf_counter

from fastapi import Request, Response, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware

from ..core.config import settings
from ..localisation.context_detection import CulturalContextDetector
from ..lib.metrics import MetricsRecorder, LocalisationMetric

logger = logging.getLogger(__name__)

# Context variables for request-scoped localisation
current_language: ContextVar[Optional[str]] = ContextVar('current_language', default=None)
current_cultural_context: ContextVar[Optional[str]] = ContextVar('current_cultural_context', default=None)
localisation_context: ContextVar[Optional[Dict]] = ContextVar('localisation_context', default=None)


class LocalisationContext:
    """Context manager for localisation settings within a request."""

    def __init__(self, language: str = "en", cultural_context: str = "nigerian"):
        self.language = language
        self.cultural_context = cultural_context
        self._previous_language = None
        self._previous_cultural_context = None
        self._previous_localisation_context = None

    def __enter__(self):
        """Enter the localisation context."""
        # Store previous values
        self._previous_language = current_language.get(None)
        self._previous_cultural_context = current_cultural_context.get(None)
        self._previous_localisation_context = localisation_context.get(None)

        # Set new values
        current_language.set(self.language)
        current_cultural_context.set(self.cultural_context)
        localisation_context.set({
            "language": self.language,
            "cultural_context": self.cultural_context,
            "timestamp": None,  # Will be set by middleware
        })

        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit the localisation context and restore previous values."""
        if self._previous_language is not None:
            current_language.set(self._previous_language)
        else:
            current_language.set(None)

        if self._previous_cultural_context is not None:
            current_cultural_context.set(self._previous_cultural_context)
        else:
            current_cultural_context.set(None)

        if self._previous_localisation_context is not None:
            localisation_context.set(self._previous_localisation_context)
        else:
            localisation_context.set(None)


class LocalisationMiddleware(BaseHTTPMiddleware):
    """
    Middleware for handling dynamic language switching and cultural context.

    Features:
    - Detects language from Accept-Language header, session, or user preferences
    - Sets cultural context based on user profile or defaults
    - Provides localisation services throughout the request lifecycle
    - Handles fallback to default language (English)
    - Supports dynamic language switching during sessions
    """

    def __init__(
        self,
        app,
        default_language: str = "en",
        default_cultural_context: str = "nigerian",
        supported_languages: Optional[List[str]] = None,
        supported_cultural_contexts: Optional[List[str]] = None,
    ):
        super().__init__(app)
        self.default_language = default_language
        self.default_cultural_context = default_cultural_context
        self.supported_languages = supported_languages or ["en"]
        self.supported_cultural_contexts = supported_cultural_contexts or [
            "nigerian", "west_african", "formal_business"
        ]

        self.context_detector = CulturalContextDetector(
            default_context=self.default_cultural_context,
            supported_contexts=self.supported_cultural_contexts,
        )

        # Import localisation components
        try:
            from ..localisation.en import english_pack
            from ..localisation.accent_handler import accent_handler
            from ..localisation.cultural_messages import cultural_handler

            self.english_pack = english_pack
            self.accent_handler = accent_handler
            self.cultural_handler = cultural_handler
        except ImportError as e:
            logger.warning(f"Could not import localisation components: {e}")
            self.english_pack = None
            self.accent_handler = None
            self.cultural_handler = None

    async def dispatch(self, request: Request, call_next):
        """Process the request with localisation context."""

        # Detect language and cultural context
        language = self._detect_language(request)
        baseline_context, baseline_source, explicit = self._detect_cultural_context_details(request)
        agent_id = getattr(request.state, "agent_id", None) or request.headers.get("X-Agent-Id")
        session_id = await self.context_detector.extract_session_identifier(request)

        detection_start = perf_counter()
        detection_result = await self.context_detector.resolve(
            request,
            session_id=session_id,
            agent_id=agent_id,
            baseline_context=baseline_context,
            baseline_source=baseline_source,
            explicit_source=explicit,
        )
        detection_duration_ms = (perf_counter() - detection_start) * 1000
        request.state.localisation_detection_ms = detection_duration_ms

        MetricsRecorder.record_localisation(
            LocalisationMetric(
                latency_ms=detection_duration_ms,
                source=detection_result.source,
                persisted=detection_result.persisted,
                had_session=bool(session_id),
                had_agent=bool(agent_id),
            )
        )

        if (
            detection_duration_ms > settings.LOCALISATION_LATENCY_TARGET_MS
        ):
            logger.warning(
                "Localisation detection latency %.2fms exceeded target %.2fms",
                detection_duration_ms,
                settings.LOCALISATION_LATENCY_TARGET_MS,
            )

        if (
            detection_result.source == "default"
            and (session_id or agent_id)
        ):
            logger.warning(
                "Localisation fell back to default despite identifiers",
                extra={
                    "session_id": session_id,
                    "agent_id": agent_id,
                },
            )

        cultural_context = detection_result.context

        # Validate detected values
        language = self._validate_language(language)
        cultural_context = self._validate_cultural_context(cultural_context)

        # Set up localisation context for the request
        with LocalisationContext(language=language, cultural_context=cultural_context) as ctx:
            # Add localisation info to request state
            request.state.language = language
            request.state.cultural_context = cultural_context
            request.state.localisation_context = ctx
            request.state.cultural_context_source = detection_result.source
            request.state.localisation_detection_ms = detection_duration_ms
            if detection_result.session_id:
                request.state.localisation_session_id = detection_result.session_id

            # Process the request
            try:
                response = await call_next(request)

                # Add localisation headers to response
                self._add_localisation_headers(
                    response,
                    language,
                    cultural_context,
                    detection_result.source,
                    detection_duration_ms,
                )

                return response

            except HTTPException as exc:  # pragma: no cover - managed upstream
                raise exc
            except Exception as exc:  # pragma: no cover - managed upstream
                logger.exception("Unhandled exception in localisation pipeline")
                raise

    def _detect_language(self, request: Request) -> str:
        """Detect the preferred language from the request."""

        # 1. Check for explicit language parameter
        if hasattr(request.query_params, 'get') and request.query_params.get('lang'):
            return request.query_params.get('lang')

        # 2. Check Accept-Language header
        accept_language = request.headers.get('Accept-Language', '')
        if accept_language:
            # Parse Accept-Language header (e.g., "en-US,en;q=0.9")
            languages = [lang.split(';')[0].split('-')[0] for lang in accept_language.split(',')]
            for lang in languages:
                if lang in self.supported_languages:
                    return lang

        # 3. Check user session (if available)
        # This would typically come from your session management system
        # For now, we'll skip this and use default

        # 4. Check user profile (if available)
        # This would come from your user management system

        # 5. Default to configured default
        return self.default_language

    def _detect_cultural_context(self, request: Request) -> str:
        """Backward-compatible cultural context detection used in tests."""

        context, _, _ = self._detect_cultural_context_details(request)
        return context or self.default_cultural_context

    def _detect_cultural_context_details(self, request: Request) -> Tuple[Optional[str], Optional[str], bool]:
        """Detect cultural context with source metadata and explicit flag."""

        if hasattr(request.query_params, "get"):
            culture_param = request.query_params.get("culture")
            if culture_param:
                return culture_param, "query_param", True

        header_override = request.headers.get("X-Cultural-Context") or request.headers.get("X-Culture")
        if header_override:
            return header_override, "header_override", True

        user_agent = request.headers.get('User-Agent', '').lower()
        if user_agent and any(term in user_agent for term in ['nigeria', 'lagos', 'naija']):
            return 'nigerian', 'user_agent', False
        if user_agent and any(term in user_agent for term in ['ghana', 'accra', 'west africa']):
            return 'west_african', 'user_agent', False

        return None, None, False

    def _validate_language(self, language: str) -> str:
        """Validate and normalize the language code."""
        if not language:
            return self.default_language

        # Normalize language code
        language = language.lower().strip()

        # Check if supported
        if language in self.supported_languages:
            return language

        # Check for language variants (e.g., en-US -> en)
        base_language = language.split('-')[0]
        if base_language in self.supported_languages:
            return base_language

        logger.warning(f"Unsupported language '{language}', falling back to '{self.default_language}'")
        return self.default_language

    def _validate_cultural_context(self, cultural_context: str) -> str:
        """Validate and normalize the cultural context."""
        if not cultural_context:
            return self.default_cultural_context

        # Normalize cultural context
        cultural_context = cultural_context.lower().strip()

        # Check if supported
        if cultural_context in self.supported_cultural_contexts:
            return cultural_context

        logger.warning(f"Unsupported cultural context '{cultural_context}', falling back to '{self.default_cultural_context}'")
        return self.default_cultural_context

    def _add_localisation_headers(
        self,
        response: Response,
        language: str,
        cultural_context: str,
        source: Optional[str],
        detection_latency_ms: Optional[float],
    ) -> None:
        """Add localisation headers to the response."""

        response.headers['X-Localisation-Language'] = language
        response.headers['X-Localisation-Cultural-Context'] = cultural_context
        response.headers['X-Localisation-Supported-Languages'] = ','.join(self.supported_languages)
        response.headers['X-Localisation-Supported-Contexts'] = ','.join(self.supported_cultural_contexts)
        if source:
            response.headers['X-Localisation-Context-Source'] = source
        if detection_latency_ms is not None:
            response.headers['X-Localisation-Latency'] = f"{detection_latency_ms:.2f}"

    async def _handle_localisation_error(self, error: Exception, cultural_context: str) -> Response:
        """Handle errors with culturally appropriate responses."""
        from fastapi.responses import JSONResponse

        error_messages = {
            "nigerian": {
                "title": "System Error",
                "message": "E kaasan, system wa n ni problem. Jọwọ ẹ tun gbiyanju later.",
                "details": "Sorry for the inconvenience. Please try again later or contact support."
            },
            "west_african": {
                "title": "System Error",
                "message": "We apologize for the technical issue. Please try again shortly.",
                "details": "Our technical team has been notified of this issue."
            },
            "formal_business": {
                "title": "System Unavailable",
                "message": "We sincerely apologize for the temporary service interruption.",
                "details": "Please contact our technical support team for immediate assistance."
            }
        }

        error_info = error_messages.get(cultural_context, error_messages[self.default_cultural_context])

        return JSONResponse(
            status_code=500,
            content={
                "error": "INTERNAL_ERROR",
                "message": error_info["message"],
                "title": error_info["title"],
                "details": error_info["details"],
                "cultural_context": cultural_context,
                "timestamp": None  # Would be set to current time
            }
        )


def get_current_language() -> Optional[str]:
    """Get the current language from the request context."""
    return current_language.get(None)


def get_current_cultural_context() -> Optional[str]:
    """Get the current cultural context from the request context."""
    return current_cultural_context.get(None)


def get_localisation_context() -> Optional[Dict]:
    """Get the current localisation context from the request context."""
    return localisation_context.get(None)


def require_language(language: str) -> str:
    """Require a specific language for the current context."""
    current = get_current_language()
    if current != language:
        logger.warning(f"Language mismatch: requested {language}, current {current}")
    return language


def require_cultural_context(cultural_context: str) -> str:
    """Require a specific cultural context for the current context."""
    current = get_current_cultural_context()
    if current != cultural_context:
        logger.warning(f"Cultural context mismatch: requested {cultural_context}, current {current}")
    return cultural_context


@contextmanager
def temporary_language(language: str, cultural_context: Optional[str] = None):
    """Temporarily switch to a different language for a code block."""
    current_lang = get_current_language()
    current_culture = get_current_cultural_context()

    try:
        with LocalisationContext(language=language, cultural_context=cultural_context or current_culture):
            yield
    finally:
        if current_lang is not None or current_culture is not None:
            with LocalisationContext(language=current_lang or "en", cultural_context=current_culture or "nigerian"):
                pass


def format_message_for_culture(message: str, cultural_context: Optional[str] = None) -> str:
    """Format a message for the specified cultural context."""
    if not cultural_context:
        cultural_context = get_current_cultural_context() or "nigerian"

    # This is a simplified implementation
    # In a full implementation, this would use the cultural message handler
    # to format messages appropriately for the cultural context
    return message


def get_localised_error_message(error_type: str, **kwargs) -> Dict[str, str]:
    """Get a culturally appropriate error message for the current context."""
    from ..localisation.cultural_messages import ErrorContext, cultural_handler

    cultural_context = get_current_cultural_context() or "nigerian"

    try:
        error_context = ErrorContext(error_type)
        return cultural_handler.get_cultural_error_message(error_context, cultural_context, **kwargs)
    except ValueError:
        # Fallback for unknown error types
        return cultural_handler.get_cultural_error_message(
            ErrorContext.SYSTEM_UNAVAILABLE, cultural_context, **kwargs
        )
