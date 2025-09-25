"""SessionService for multi-channel session management."""

import time
import uuid
import json
from typing import Dict, List, Optional
from datetime import datetime, timedelta

from src.core.config import settings
from src.models.agent import Agent, AgentSession, ChannelType, SessionContext, SessionStatus, Message
from src.lib.graceful_degradation import GracefulDegradationService


class SessionService:
    """Service for managing multi-channel conversation sessions."""

    def __init__(self):
        self.degradation_service = None
        self._sessions: Dict[str, AgentSession] = {}

    async def get_instance(self) -> "SessionService":
        """Get singleton instance with dependencies initialized."""
        if self.degradation_service is None:
            self.degradation_service = await GracefulDegradationService.get_instance()
        return self

    async def create_session(self, agent_id: str, channel: ChannelType) -> AgentSession:
        """Create a new session for an agent."""
        session_id = str(uuid.uuid4())

        session = AgentSession(
            id=session_id,
            agentId=agent_id,
            channel=channel,
            startTime=datetime.utcnow(),
            status=SessionStatus.ACTIVE,
            context=SessionContext(
                currentIntent=None,
                activeEntities=[],
                lastResponse="",
                pendingActions=[]
            )
        )

        self._sessions[session_id] = session
        return session

    async def get_session(self, session_id: str, agent_id: str) -> Optional[AgentSession]:
        """Get session by ID if agent has access."""
        session = self._sessions.get(session_id)

        if session and session.agentId == agent_id:
            # Check if session is expired
            if self._is_session_expired(session):
                session.status = SessionStatus.EXPIRED
                return session
            return session

        # Try to load from persistent storage
        return await self._load_session_from_storage(session_id, agent_id)

    async def update_session_context(self, session_id: str, context: SessionContext) -> bool:
        """Update session context."""
        if session_id in self._sessions:
            self._sessions[session_id].context = context
            return True
        return False

    async def add_message(self, session_id: str, message: Message) -> bool:
        """Add a message to a session."""
        if session_id in self._sessions:
            session = self._sessions[session_id]
            session.conversationHistory.append(message)

            # Enforce maximum messages per session
            if len(session.conversationHistory) > settings.MAX_SESSION_MESSAGES:
                session.conversationHistory = session.conversationHistory[-settings.MAX_SESSION_MESSAGES:]

            # Update context based on message
            await self._update_context_from_message(session, message)
            return True
        return False

    async def get_session_messages(self, session_id: str, agent_id: str, limit: int = 50) -> List[Message]:
        """Get messages from a session."""
        session = await self.get_session(session_id, agent_id)

        if not session:
            return []

        messages = session.conversationHistory
        return messages[-limit:] if len(messages) > limit else messages

    async def switch_channel(self, session_id: str, agent_id: str, new_channel: ChannelType) -> Optional[AgentSession]:
        """Switch session to a different channel while preserving context."""
        session = await self.get_session(session_id, agent_id)

        if not session:
            return None

        # Update channel while preserving context
        session.channel = new_channel
        return session

    async def end_session(self, session_id: str, agent_id: str) -> bool:
        """End a session."""
        session = await self.get_session(session_id, agent_id)

        if not session:
            return False

        session.status = SessionStatus.COMPLETED
        session.endTime = datetime.utcnow()

        # Persist session to storage
        await self._persist_session(session)
        return True

    def _is_session_expired(self, session: AgentSession) -> bool:
        """Check if a session has expired due to inactivity."""
        if session.status != SessionStatus.ACTIVE:
            return False

        # Check if session has been inactive for too long
        last_activity = self._get_session_last_activity(session)
        timeout_threshold = datetime.utcnow() - timedelta(minutes=settings.SESSION_TIMEOUT_MINUTES)

        return last_activity < timeout_threshold

    def _get_session_last_activity(self, session: AgentSession) -> datetime:
        """Get the timestamp of the last activity in a session."""
        if session.conversationHistory:
            return session.conversationHistory[-1].timestamp
        return session.startTime

    async def _update_context_from_message(self, session: AgentSession, message: Message):
        """Update session context based on a new message."""
        context = session.context

        # Update current intent based on message content
        if message.type == "user":
            context.currentIntent = self._infer_intent(message.content)
            context.lastResponse = ""

            # Extract entities from message
            entities = self._extract_entities_from_message(message.content)
            context.activeEntities.extend(entities)

            # Limit active entities
            if len(context.activeEntities) > 10:
                context.activeEntities = context.activeEntities[-10:]
        else:
            # This is an assistant response
            context.lastResponse = message.content

    def _infer_intent(self, message: str) -> Optional[str]:
        """Infer the user's intent from their message."""
        message_lower = message.lower()

        if any(keyword in message_lower for keyword in ["track", "status", "where"]):
            return "track_container"
        elif any(keyword in message_lower for keyword in ["help", "what", "how"]):
            return "get_help"
        elif any(keyword in message_lower for keyword in ["book", "schedule", "arrange"]):
            return "book_service"
        else:
            return "general_inquiry"

    def _extract_entities_from_message(self, message: str) -> List[Dict]:
        """Extract entities from a message."""
        entities = []

        # Simple entity extraction - look for container and BL patterns
        import re

        # Container IDs (EFLU followed by 7 digits)
        container_pattern = r'EFLU(\d{7})'
        containers = re.findall(container_pattern, message.upper())
        for container in containers:
            entities.append({
                "type": "container",
                "id": f"EFLU{container}",
                "confidence": 0.95
            })

        # BL numbers (ABC followed by 7 digits)
        bl_pattern = r'ABC(\d{7})'
        bl_numbers = re.findall(bl_pattern, message.upper())
        for bl in bl_numbers:
            entities.append({
                "type": "bl",
                "id": f"ABC{bl}",
                "confidence": 0.95
            })

        return entities

    async def _load_session_from_storage(self, session_id: str, agent_id: str) -> Optional[AgentSession]:
        """Load session from persistent storage."""
        # This would typically load from Redis or database
        # For now, return None
        return None

    async def _persist_session(self, session: AgentSession):
        """Persist session to storage."""
        # This would typically save to Redis or database
        # For now, just keep in memory
        pass

    async def cleanup_expired_sessions(self):
        """Clean up expired sessions."""
        current_time = datetime.utcnow()
        expired_sessions = []

        for session_id, session in self._sessions.items():
            if self._is_session_expired(session):
                session.status = SessionStatus.EXPIRED
                expired_sessions.append(session_id)

        # Remove expired sessions
        for session_id in expired_sessions:
            del self._sessions[session_id]

    def get_session_stats(self) -> Dict:
        """Get session statistics."""
        total_sessions = len(self._sessions)
        active_sessions = len([s for s in self._sessions.values() if s.status == SessionStatus.ACTIVE])
        expired_sessions = len([s for s in self._sessions.values() if s.status == SessionStatus.EXPIRED])

        return {
            "total_sessions": total_sessions,
            "active_sessions": active_sessions,
            "expired_sessions": expired_sessions
        }
