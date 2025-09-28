"""Utilities for resolving cultural context preferences across channels."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from typing import Awaitable, Callable, Optional, Sequence

from fastapi import Request

from src.services.session_service import SessionService

logger = logging.getLogger(__name__)


@dataclass
class CulturalContextResult:
    """Result of cultural context resolution."""

    context: str
    source: str
    session_id: Optional[str]
    persisted: bool = False


class CulturalContextDetector:
    """Resolve cultural context preferences from request metadata."""

    def __init__(
        self,
        default_context: str = "nigerian",
        supported_contexts: Optional[Sequence[str]] = None,
        session_provider: Optional[Callable[[], Awaitable[SessionService]]] = None,
    ) -> None:
        self.default_context = default_context
        self.supported_contexts = tuple(supported_contexts or [
            "nigerian",
            "west_african",
            "formal_business"
        ])
        self._supported_lookup = {ctx.lower(): ctx for ctx in self.supported_contexts}
        self._session_provider = session_provider
        self._session_service: Optional[SessionService] = None

    async def resolve(
        self,
        request: Request,
        *,
        session_id: Optional[str],
        agent_id: Optional[str],
        baseline_context: Optional[str],
        baseline_source: Optional[str],
        explicit_source: bool = False,
    ) -> CulturalContextResult:
        """Resolve cultural context for the current request."""

        normalized_baseline = self._normalize_context(baseline_context)

        if explicit_source and normalized_baseline:
            persisted = await self._persist_preference(session_id, agent_id, normalized_baseline)
            return CulturalContextResult(
                context=normalized_baseline,
                source=baseline_source or "explicit",
                session_id=session_id,
                persisted=persisted,
            )

        # Session preference should take precedence when available.
        session_pref = await self._get_session_preference(session_id, agent_id)
        if session_pref:
            return CulturalContextResult(
                context=session_pref,
                source="session",
                session_id=session_id,
                persisted=False,
            )

        # Agent profile preference (JWT claim or request state injection).
        agent_pref = self._normalize_context(self._extract_agent_preference(request))
        if agent_pref:
            persisted = await self._persist_preference(session_id, agent_id, agent_pref)
            return CulturalContextResult(
                context=agent_pref,
                source="agent_profile",
                session_id=session_id,
                persisted=persisted,
            )

        # Channel metadata (voice/call headers).
        channel_pref = self._normalize_context(self._extract_channel_preference(request))
        if channel_pref:
            persisted = await self._persist_preference(session_id, agent_id, channel_pref)
            return CulturalContextResult(
                context=channel_pref,
                source="channel_metadata",
                session_id=session_id,
                persisted=persisted,
            )

        # Accept-Language signals.
        language_pref = self._normalize_context(self._infer_from_accept_language(request))
        if language_pref:
            persisted = await self._persist_preference(session_id, agent_id, language_pref)
            return CulturalContextResult(
                context=language_pref,
                source="accept_language",
                session_id=session_id,
                persisted=persisted,
            )

        # User agent heuristics from baseline (if provided) or fallback to detected default.
        if normalized_baseline:
            persisted = await self._persist_preference(session_id, agent_id, normalized_baseline)
            return CulturalContextResult(
                context=normalized_baseline,
                source=baseline_source or "heuristic",
                session_id=session_id,
                persisted=persisted,
            )

        # Final fallback to configured default.
        persisted = await self._persist_preference(session_id, agent_id, self.default_context)
        return CulturalContextResult(
            context=self.default_context,
            source="default",
            session_id=session_id,
            persisted=persisted,
        )

    async def _get_session_preference(
        self,
        session_id: Optional[str],
        agent_id: Optional[str],
    ) -> Optional[str]:
        if not session_id and not agent_id:
            return None

        service = await self._ensure_session_service()
        if not service:
            return None

        try:
            preference = await service.get_cultural_preference(session_id, agent_id)
            return self._normalize_context(preference)
        except Exception as exc:  # pragma: no cover - defensive logging
            logger.warning("Failed to read session cultural preference: %s", exc)
            return None

    async def _persist_preference(
        self,
        session_id: Optional[str],
        agent_id: Optional[str],
        preference: Optional[str],
    ) -> bool:
        preference = self._normalize_context(preference)
        if not preference:
            return False

        service = await self._ensure_session_service()
        if not service:
            return False

        try:
            return await service.update_cultural_preference(session_id, agent_id, preference)
        except Exception as exc:  # pragma: no cover - defensive logging
            logger.warning("Failed to persist cultural preference: %s", exc)
            return False

    async def _ensure_session_service(self) -> Optional[SessionService]:
        if self._session_service is not None:
            return self._session_service

        try:
            if self._session_provider:
                service = await self._session_provider()
            else:
                service = await SessionService().get_instance()
        except Exception as exc:  # pragma: no cover - defensive logging
            logger.warning("Unable to initialize session service for localisation: %s", exc)
            return None

        self._session_service = service
        return self._session_service

    def _normalize_context(self, context: Optional[str]) -> Optional[str]:
        if not context:
            return None

        normalized = context.strip().lower()
        return self._supported_lookup.get(normalized)

    def _extract_agent_preference(self, request: Request) -> Optional[str]:
        token_payload = getattr(request.state, "token_payload", None)
        if isinstance(token_payload, dict):
            preference = token_payload.get("cultural_context") or token_payload.get("preferred_culture")
            if preference:
                return preference

        return getattr(request.state, "cultural_preference", None)

    def _extract_channel_preference(self, request: Request) -> Optional[str]:
        # Voice gateway metadata
        caller_country = request.headers.get("X-Caller-Country") or request.headers.get("X-Twilio-Caller-Country")
        if caller_country:
            caller_country = caller_country.strip().upper()
            if caller_country in {"NG", "NGA"}:
                return "nigerian"
            if caller_country in {"GH", "GHA", "SL", "SLE", "LR", "LBR", "BJ", "BEN"}:
                return "west_african"

        channel_hint = request.headers.get("X-Channel-Culture") or request.headers.get("X-Preferred-Culture")
        if channel_hint:
            return channel_hint

        return None

    def _infer_from_accept_language(self, request: Request) -> Optional[str]:
        header = request.headers.get("Accept-Language", "")
        if not header:
            return None

        languages = [item.split(";")[0].strip().lower().replace("_", "-") for item in header.split(",")]
        for language in languages:
            if language in {"en-ng", "ig-ng", "yo-ng", "ha-ng"}:
                return "nigerian"
            if language in {"en-gh", "en-sl", "en-lr", "en-bj", "fr-sn", "fr-ci"}:
                return "west_african"
            if language in {"en-gb", "en-uk", "en-us", "fr-fr"}:
                return "formal_business"
        return None

    async def extract_session_identifier(self, request: Request) -> Optional[str]:
        """Extract session identifier from headers, query parameters, or JSON payload."""

        header_session = request.headers.get("X-Session-Id") or request.headers.get("X-Conversation-Id")
        if header_session:
            return header_session

        query_session = request.query_params.get("sessionId") if hasattr(request, "query_params") else None
        if query_session:
            return query_session

        # Attempt to read JSON payload for session identifier.
        if request.headers.get("content-type", "").startswith("application/json"):
            try:
                body_bytes = await request.body()
                if not body_bytes:
                    return None

                payload = json.loads(body_bytes.decode("utf-8"))
                session_id = payload.get("sessionId") or payload.get("session_id")

                # Rehydrate the body so downstream handlers can consume it.
                async def receive() -> dict:
                    return {"type": "http.request", "body": body_bytes, "more_body": False}

                request._receive = receive  # type: ignore[attr-defined]
                return session_id
            except (ValueError, json.JSONDecodeError):
                return None
        return None
