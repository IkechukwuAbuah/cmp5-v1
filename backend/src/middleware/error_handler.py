"""Error handling middleware that emits culturally aware responses."""

import time
import logging
from typing import Callable, Dict, Optional

from fastapi import HTTPException, Request, Response, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from src.core.config import settings
from src.localisation.cultural_messages import (
    CulturalMessageHandler,
    ErrorContext,
)


logger = logging.getLogger(__name__)


class ErrorHandlerMiddleware(BaseHTTPMiddleware):
    """Middleware for handling errors with culturally appropriate responses."""

    def __init__(self, app, *args, **kwargs) -> None:  # type: ignore[override]
        super().__init__(app, *args, **kwargs)
        self._message_handler = CulturalMessageHandler()

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request with error handling."""
        start_time = time.time()

        try:
            response = await call_next(request)
            duration = time.time() - start_time
            logger.debug(
                "✅ %s %s -> %s in %.2fs",
                request.method,
                request.url.path,
                response.status_code,
                duration,
            )
            return response

        except HTTPException as exc:
            duration = time.time() - start_time
            logger.warning(
                "⚠️ %s %s -> HTTPException %s in %.2fs: %s",
                request.method,
                request.url.path,
                exc.status_code,
                duration,
                exc.detail,
            )
            payload = self._build_cultural_payload(request, exc)
            response = JSONResponse(status_code=exc.status_code, content=payload)
            self._apply_localisation_headers(response, request)
            return response

        except Exception as exc:  # pragma: no cover - defensive safety net
            duration = time.time() - start_time
            logger.exception(
                "❌ %s %s -> Unhandled error in %.2fs",
                request.method,
                request.url.path,
                duration,
            )
            payload = self._build_cultural_payload(
                request,
                HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, detail={}),
                fallback_context=ErrorContext.SYSTEM_UNAVAILABLE,
                error=exc,
            )
            response = JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content=payload)
            self._apply_localisation_headers(response, request)
            return response

    def _build_cultural_payload(
        self,
        request: Request,
        exc: HTTPException,
        *,
        fallback_context: ErrorContext = ErrorContext.SYSTEM_UNAVAILABLE,
        error: Optional[Exception] = None,
    ) -> Dict[str, object]:
        detail = exc.detail if isinstance(exc.detail, dict) else {}
        context_value = detail.get("context") or detail.get("error_context")
        params = detail.get("params", {}) if isinstance(detail, dict) else {}

        try:
            error_context = ErrorContext(context_value) if context_value else fallback_context
        except ValueError:
            logger.debug("Unknown error context '%s', using fallback", context_value)
            error_context = fallback_context

        cultural_context = getattr(
            request.state,
            "cultural_context",
            settings.DEFAULT_CULTURAL_CONTEXT,
        )

        message_data = self._message_handler.get_cultural_error_message(
            error_context,
            cultural_context,
            **params,
        )

        error_code = detail.get("code") if isinstance(detail, dict) else None
        if not error_code:
            error_code = error_context.name

        payload: Dict[str, object] = {
            "error": error_code,
            "message": message_data["primary_message"],
            "alternatives": message_data["alternative_messages"],
            "nextSteps": message_data["next_steps"],
            "tone": message_data["tone"],
            "requiresConfirmation": message_data["requires_confirmation"],
            "culturalContext": cultural_context,
            "source": getattr(request.state, "cultural_context_source", "auto"),
            "timestamp": time.time(),
        }

        if params:
            payload["details"] = params

        if error is not None:
            payload["internalError"] = str(error)

        return payload

    def _apply_localisation_headers(self, response: Response, request: Request) -> None:
        language = getattr(request.state, "language", settings.DEFAULT_LANGUAGE)
        cultural_context = getattr(request.state, "cultural_context", settings.DEFAULT_CULTURAL_CONTEXT)
        source = getattr(request.state, "cultural_context_source", "auto")
        latency = getattr(request.state, "localisation_detection_ms", None)

        response.headers['X-Localisation-Language'] = language
        response.headers['X-Localisation-Cultural-Context'] = cultural_context
        response.headers['X-Localisation-Context-Source'] = str(source)
        if latency is not None:
            response.headers['X-Localisation-Latency'] = f"{latency:.2f}"
