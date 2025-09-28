"""Service for multi-channel routing between voice and chat."""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from src.models.agent import ChannelType
from src.services.session_service import SessionService
from src.voice.session_continuity import get_voice_continuity
from src.chat.chat_continuity import ChatContinuityManager


logger = logging.getLogger(__name__)


class ChannelRouterService:
    """Route interactions between voice and chat while preserving context."""

    def __init__(self):
        self.session_service: Optional[SessionService] = None
        self.chat_continuity: Optional[ChatContinuityManager] = None

    async def get_instance(self) -> "ChannelRouterService":
        if self.session_service is None:
            self.session_service = await SessionService().get_instance()
        if self.chat_continuity is None:
            self.chat_continuity = await ChatContinuityManager().get_instance()
        return self

    async def route_to_voice(
        self, session_id: str, agent_id: str, context_override: Optional[Dict] = None
    ) -> Dict[str, Any]:
        if not self.session_service:
            await self.get_instance()

        router_state = await get_voice_continuity()
        session = await self.session_service.get_session(session_id, agent_id)
        if not session:
            session = await self.session_service.create_session(agent_id, ChannelType.VOICE)
            session_id = session.id
        else:
            session_id = session.id

        session.channel = ChannelType.VOICE
        session.context.preferredChannel = ChannelType.VOICE
        await self.session_service.update_session_context(session.id, session.context)

        voice_state = await router_state.sync_from_chat(
            session.id, agent_id, session.context, context_override
        )
        voice_context = voice_state.get_relevant_context() or {}
        recent_entities = voice_context.get("recent_entities", [])
        voice_context["recent_entities"] = [
            entity.model_dump() if hasattr(entity, "model_dump") else entity for entity in recent_entities
        ]
        voice_context["preferredChannel"] = ChannelType.VOICE.value
        voice_context["language"] = session.context.preferredLanguage
        voice_context["culturalContext"] = session.context.preferredCulturalContext

        logger.info("Routed session %s to voice", session_id)
        return {
            "sessionId": voice_state.session_id,
            "channel": ChannelType.VOICE.value,
            "context": voice_context,
        }

    async def route_to_chat(
        self, session_id: str, agent_id: str, voice_context: Optional[Dict]
    ) -> Dict[str, Any]:
        if not self.chat_continuity or not self.session_service:
            await self.get_instance()

        session = await self.session_service.get_session(session_id, agent_id)
        if not session:
            session = await self.session_service.create_session(agent_id, ChannelType.CHAT)
            session_id = session.id
        else:
            session_id = session.id

        session.channel = ChannelType.CHAT
        session.context.preferredChannel = ChannelType.CHAT
        await self.session_service.update_session_context(session.id, session.context)

        synced_session = await self.chat_continuity.continue_from_voice(
            session.id, agent_id, voice_context or {}
        )
        if synced_session:
            session = synced_session

        session_context = session.context
        response_context = {
            "currentIntent": session_context.currentIntent,
            "activeEntities": [entity.model_dump() for entity in session_context.activeEntities],
            "pendingActions": list(session_context.pendingActions),
            "lastResponse": session_context.lastResponse,
            "preferredChannel": ChannelType.CHAT.value,
            "language": session_context.preferredLanguage,
            "culturalContext": session_context.preferredCulturalContext,
        }

        logger.info("Routed session %s to chat", session_id)
        return {
            "sessionId": session.id,
            "channel": ChannelType.CHAT.value,
            "context": response_context,
        }


__all__ = ["ChannelRouterService"]
