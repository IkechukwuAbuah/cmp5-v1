"""Chat session continuity and context preservation."""

from __future__ import annotations

import logging
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Deque, Dict, Iterable, List, Optional

from src.models.agent import (
    AgentSession,
    SessionContext,
    Message,
    ChannelType,
    EntityReference,
)
from src.services.session_service import SessionService


logger = logging.getLogger(__name__)


@dataclass
class ChatTurn:
    """Represents a single turn in the chat conversation."""

    user_message: Message
    assistant_message: Optional[Message] = None
    timestamp: datetime = field(default_factory=datetime.utcnow)
    entities_mentioned: List[EntityReference] = field(default_factory=list)


class ChatContinuityManager:
    """Maintain chat session continuity and shared context."""

    def __init__(self):
        self.session_service: Optional[SessionService] = None
        self.turn_history: Dict[str, Deque[ChatTurn]] = {}
        self.session_timeout = timedelta(minutes=30)

    async def get_instance(self) -> "ChatContinuityManager":
        if self.session_service is None:
            self.session_service = await SessionService().get_instance()
        return self

    async def record_turn(
        self,
        session_id: str,
        agent_id: str,
        user_message: Message,
        assistant_message: Optional[Message],
        entities: Optional[List[Dict]] = None,
    ) -> None:
        """Record a new conversation turn and update session context."""

        history = self.turn_history.setdefault(session_id, deque(maxlen=10))
        turn = ChatTurn(user_message=user_message, assistant_message=assistant_message)
        if entities:
            turn.entities_mentioned.extend(self._normalize_entities(entities))
        history.append(turn)

        await self._update_session_context(session_id, agent_id, entities)

    async def hydrate_context(
        self, session_id: str, agent_id: str
    ) -> Optional[SessionContext]:
        session = await self.session_service.get_session(session_id, agent_id)
        if not session:
            return None
        return session.context

    async def continue_from_voice(
        self,
        session_id: str,
        agent_id: str,
        voice_context: Dict[str, List[Dict]],
    ) -> Optional[AgentSession]:
        """Synchronize context from voice channel when user switches to chat."""

        session = await self.session_service.get_session(session_id, agent_id)
        if not session:
            session = await self.session_service.create_session(agent_id, ChannelType.CHAT)
            session.id = session_id

        context = session.context
        context.currentIntent = voice_context.get("current_intent")
        voice_entities = voice_context.get("recent_entities", [])
        if voice_entities:
            context.activeEntities.extend(self._normalize_entities(voice_entities))
        context.pendingActions.extend(voice_context.get("pending_clarifications", []))
        await self.session_service.update_session_context(session_id, context)

        return session

    async def cleanup_expired_sessions(self) -> None:
        now = datetime.utcnow()
        expired = [
            session_id
            for session_id, history in self.turn_history.items()
            if history and now - history[-1].timestamp > self.session_timeout
        ]

        for session_id in expired:
            logger.info("Cleaning up expired chat session %s", session_id)
            del self.turn_history[session_id]

    async def _update_session_context(
        self, session_id: str, agent_id: str, entities: Optional[List[Dict]]
    ) -> None:
        session = await self.session_service.get_session(session_id, agent_id)
        if not session:
            return

        context = session.context
        if entities:
            references = self._normalize_entities(entities)
            context.activeEntities.extend(references)
            # Deduplicate while preserving order and limit to last 10
            deduped: List[EntityReference] = []
            seen_ids = set()
            for ref in context.activeEntities[::-1]:
                key = (ref.type, ref.id)
                if key in seen_ids:
                    continue
                seen_ids.add(key)
                deduped.append(ref)
            context.activeEntities = list(reversed(deduped))[-10:]

        context.lastResponse = session.conversationHistory[-1].content if session.conversationHistory else ""
        await self.session_service.update_session_context(session_id, context)

    def _normalize_entities(self, entities: Iterable) -> List[EntityReference]:
        normalized: List[EntityReference] = []
        for entity in entities:
            if isinstance(entity, EntityReference):
                normalized.append(entity)
                continue

            if isinstance(entity, dict):
                try:
                    normalized.append(EntityReference(**entity))
                    continue
                except Exception:
                    normalized.append(
                        EntityReference(
                            type=str(entity.get("type", "unknown")),
                            id=str(entity.get("id", "")),
                            confidence=float(entity.get("confidence", 0.5)),
                        )
                    )
                    continue

            # Fallback for unknown structures such as raw strings
            normalized.append(
                EntityReference(
                    type="unknown",
                    id=str(entity),
                    confidence=0.5,
                )
            )

        return normalized


__all__ = ["ChatContinuityManager"]

