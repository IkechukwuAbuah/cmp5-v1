"""Chat interface service for natural language input."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Dict, Optional, Any, List

from src.models.agent import Agent, ChannelType
from src.models.agent_session import Message
from src.services.session_service import SessionService
from src.services.track_service import TrackService
from src.services.response_service import ResponseService
from src.chat.chat_errors import ChatErrorManager
from src.chat.chat_response import ChatResponseFormatter
from src.chat.chat_continuity import ChatContinuityManager
from src.lib.logger import get_logger
from src.lib.log_sanitizer import sanitize


logger = get_logger(__name__)


class ChatInterfaceService:
    """Handle chat channel interactions and hand off to downstream services."""

    def __init__(self):
        self.session_service: Optional[SessionService] = None
        self.track_service: Optional[TrackService] = None
        self.response_service: Optional[ResponseService] = None
        self.response_formatter: Optional[ChatResponseFormatter] = None
        self.chat_continuity: Optional[ChatContinuityManager] = None

    async def get_instance(self) -> "ChatInterfaceService":
        if self.session_service is None:
            self.session_service = await SessionService().get_instance()
        if self.track_service is None:
            self.track_service = await TrackService().get_instance()
        if self.response_service is None:
            self.response_service = await ResponseService().get_instance()
        if self.response_formatter is None:
            self.response_formatter = await ChatResponseFormatter().get_instance()
        if self.chat_continuity is None:
            self.chat_continuity = await ChatContinuityManager().get_instance()
        return self

    async def handle_message(
        self,
        session_id: Optional[str],
        agent: Agent,
        message_text: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Process a chat message and return structured response payload."""

        if not message_text or not message_text.strip():
            correlation = session_id or "chat-empty"
            hint = ChatErrorManager.get_hint("query_missing")
            error_payload = self._build_error_response("NOT_FOUND", correlation_id=correlation)
            if hint:
                error_payload["error"]["hint"] = hint
            return error_payload

        if agent is None:
            return self._build_error_response("NOT_AUTHORIZED", correlation_id=session_id)

        try:
            agent_session = (
                await self.session_service.get_session(session_id, agent.id)
                if session_id
                else None
            )
            if not agent_session:
                agent_session = await self.session_service.create_session(agent.id, ChannelType.CHAT)
                session_id = agent_session.id
            else:
                session_id = agent_session.id

            agent_session.channel = ChannelType.CHAT

            message = Message(
                id=str(uuid.uuid4()),
                type="user",
                content=message_text.strip(),
                timestamp=datetime.utcnow(),
                metadata=metadata,
            )
            await self.session_service.add_message(agent_session.id, message)

            tracking_result = await self.track_service.process_natural_language_query(
                message.content, agent=agent
            )

            containers = tracking_result.get("containers", [])
            bill_of_ladings = tracking_result.get("bill_of_ladings", [])
            raw_entities = tracking_result.get("entities", {})
            continuity_entities = self._normalize_entities(raw_entities)

            formatted = self.response_formatter.build_tracking_reply(
                query=message.content,
                containers=containers,
                bill_of_ladings=bill_of_ladings,
                entities=raw_entities,
            )

            response_message = Message(
                id=str(uuid.uuid4()),
                type="assistant",
                content=formatted["message"],
                timestamp=datetime.utcnow(),
                metadata={"entities": raw_entities, "summary": formatted.get("summary")},
            )
            await self.session_service.add_message(agent_session.id, response_message)

            if self.chat_continuity:
                await self.chat_continuity.record_turn(
                    session_id=agent_session.id,
                    agent_id=agent.id,
                    user_message=message,
                    assistant_message=response_message,
                    entities=continuity_entities,
                )

            return {
                "success": True,
                "sessionId": agent_session.id,
                "response": formatted["message"],
                "summary": formatted.get("summary"),
                "suggestions": formatted.get("suggestions", []),
                "entities": raw_entities,
                "messages": self._serialize_messages(agent_session.conversationHistory[-6:]),
            }

        except Exception as exc:
            logger.exception("Chat message handling failed: %s", exc)
            return self._build_error_response("UNKNOWN_ERROR", correlation_id=session_id)

    async def get_recent_messages(
        self, session_id: str, agent_id: str, limit: int = 10
    ) -> List[Dict[str, Any]]:
        session_messages = await self.session_service.get_session_messages(
            session_id, agent_id, limit
        )
        return self._serialize_messages(session_messages)

    def _build_error_response(self, code: str, correlation_id: Optional[str]) -> Dict[str, Any]:
        payload = ChatErrorManager.build_error_payload(code, correlation_id=correlation_id)
        return {"success": False, "sessionId": correlation_id, "error": payload}

    def _serialize_messages(self, messages: List[Message]) -> List[Dict[str, Any]]:
        serialized = []
        for msg in messages:
            serialized.append(
                {
                    "id": msg.id,
                    "type": msg.type,
                    "content": msg.content,
                    "timestamp": msg.timestamp.isoformat(),
                    "metadata": msg.metadata or {},
                }
            )
        return serialized

    def _normalize_entities(self, entities: Dict[str, List[str]]) -> List[Dict[str, Any]]:
        normalized: List[Dict[str, Any]] = []
        if not entities:
            return normalized

        for container_id in entities.get("containers", []):
            normalized.append(
                {
                    "type": "container",
                    "id": container_id,
                    "confidence": 0.9,
                }
            )

        for bl_number in entities.get("bill_of_ladings", []):
            normalized.append(
                {
                    "type": "bl",
                    "id": bl_number,
                    "confidence": 0.9,
                }
            )

        return normalized


__all__ = ["ChatInterfaceService"]
