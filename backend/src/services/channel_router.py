"""Service for multi-channel routing between voice and chat."""

from __future__ import annotations

import logging
from typing import Dict, Optional

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
    ) -> Dict[str, Optional[str]]:
        router_state = await get_voice_continuity()
        session = await self.session_service.get_session(session_id, agent_id)
        if session:
            session.channel = ChannelType.VOICE
            await self.session_service.update_session_context(session_id, session.context)

        result = await router_state.get_session_context(session_id)
        if context_override:
            result = result or {}
            result.update(context_override)

        logger.info("Routed session %s to voice", session_id)
        return result or {}

    async def route_to_chat(
        self, session_id: str, agent_id: str, voice_context: Optional[Dict]
    ) -> Dict[str, Optional[str]]:
        session = await self.session_service.get_session(session_id, agent_id)
        if session:
            session.channel = ChannelType.CHAT
            await self.session_service.update_session_context(session_id, session.context)

        if not self.chat_continuity:
            self.chat_continuity = await ChatContinuityManager().get_instance()

        synced_session = await self.chat_continuity.continue_from_voice(
            session_id, agent_id, voice_context or {}
        )
        logger.info("Routed session %s to chat", session_id)
        return {
            "sessionId": synced_session.id if synced_session else session_id,
            "channel": ChannelType.CHAT.value,
        }


__all__ = ["ChannelRouterService"]

