"""SessionService for multi-channel session management."""

import uuid
from typing import Dict, List, Optional
from datetime import datetime, timedelta

from src.core.config import settings
from src.models.agent import Agent, ChannelType
from src.models.agent_session import AgentSession, Message, SessionStatus
from src.models.session_context import SessionContext
from src.lib.graceful_degradation import GracefulDegradationService
from src.storage.redis_session_store import get_redis_session_store

import logging
logger = logging.getLogger(__name__)


class SessionService:
    """Service for managing multi-channel conversation sessions."""

    def __init__(self):
        self.degradation_service = None
        self.redis_session_store = None
        self._sessions: Dict[str, AgentSession] = {}
        self._agent_preferences: Dict[str, str] = {}
        self._agent_language_preferences: Dict[str, str] = {}

    async def get_instance(self) -> "SessionService":
        """Get singleton instance with dependencies initialized."""
        if self.degradation_service is None:
            self.degradation_service = await GracefulDegradationService.get_instance()
        if self.redis_session_store is None:
            self.redis_session_store = await get_redis_session_store()
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
                preferredChannel=channel,
                preferredLanguage=settings.DEFAULT_LANGUAGE,
                preferredCulturalContext=settings.DEFAULT_CULTURAL_CONTEXT,
                lastResponse="",
                pendingActions=[]
            )
        )

        self._sessions[session_id] = session
        return session

    async def get_session(self, session_id: str, agent_id: Optional[str] = None) -> Optional[AgentSession]:
        """Get session by ID with optional agent ownership validation."""
        session = self._sessions.get(session_id)

        if session:
            if agent_id and session.agentId != agent_id:
                return None

            if self._is_session_expired(session):
                session.status = SessionStatus.EXPIRED
                return session

            return session

        # Try to load from persistent storage when not cached
        loaded_session = await self._load_session_from_storage(session_id, agent_id)
        if loaded_session:
            # Cache loaded session for subsequent access
            self._sessions[session_id] = loaded_session
        return loaded_session

    async def update_session_context(self, session_id: str, context: SessionContext) -> bool:
        """Update session context and persist changes."""
        session = self._sessions.get(session_id)

        if not session and self.redis_session_store:
            # Attempt to hydrate from storage when not cached
            session = await self._load_session_from_storage(session_id, agent_id=None)
            if session:
                self._sessions[session_id] = session

        if not session:
            return False

        session.context = context
        await self._persist_session(session)
        return True

    async def get_language_preference(
        self,
        session_id: Optional[str],
        agent_id: Optional[str] = None,
    ) -> Optional[str]:
        """Return stored language preference for a session or agent."""

        if not session_id:
            return self._agent_language_preferences.get(agent_id) if agent_id else None

        session = await self.get_session(session_id, agent_id)
        if session and session.context and session.context.preferredLanguage:
            return session.context.preferredLanguage

        if agent_id:
            return self._agent_language_preferences.get(agent_id)

        return None

    async def get_cultural_preference(
        self,
        session_id: str,
        agent_id: Optional[str] = None
    ) -> Optional[str]:
        """Return persisted cultural context preference for a session if available."""

        if not session_id:
            return self._agent_preferences.get(agent_id) if agent_id else None

        session = await self.get_session(session_id, agent_id)
        if session and session.context and session.context.preferredCulturalContext:
            return session.context.preferredCulturalContext

        if agent_id:
            return self._agent_preferences.get(agent_id)

        return None

    async def update_cultural_preference(
        self,
        session_id: str,
        agent_id: Optional[str],
        preference: str
    ) -> bool:
        """Persist cultural context preference for the active session."""

        return await self.update_localisation_preferences(
            session_id,
            agent_id,
            cultural_context=preference,
        )

    async def update_language_preference(
        self,
        session_id: str,
        agent_id: Optional[str],
        preference: str,
    ) -> bool:
        """Persist language preference for the active session."""

        return await self.update_localisation_preferences(
            session_id,
            agent_id,
            language=preference,
        )

    async def update_localisation_preferences(
        self,
        session_id: Optional[str],
        agent_id: Optional[str],
        *,
        language: Optional[str] = None,
        cultural_context: Optional[str] = None,
    ) -> bool:
        """Persist language and cultural context preferences for the active session."""

        if language:
            language = language.strip().lower()
        if cultural_context:
            cultural_context = cultural_context.strip().lower()

        if not language and not cultural_context:
            return False

        # Persist against agent profile for continuity across sessions
        if agent_id:
            if language:
                self._agent_language_preferences[agent_id] = language
            if cultural_context:
                self._agent_preferences[agent_id] = cultural_context

        if not session_id:
            return agent_id is not None

        session = await self.get_session(session_id, agent_id)
        if not session or not session.context:
            return agent_id is not None

        updated = False

        if language and session.context.preferredLanguage != language:
            session.context.preferredLanguage = language
            updated = True

        if cultural_context and session.context.preferredCulturalContext != cultural_context:
            session.context.preferredCulturalContext = cultural_context
            updated = True

        if not updated:
            return True

        await self.update_session_context(session.id, session.context)
        return True

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
            await self._persist_session(session)
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
        if session.context:
            session.context.preferredChannel = new_channel
            await self.update_session_context(session.id, session.context)
        await self._persist_session(session)
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

    async def _load_session_from_storage(self, session_id: str, agent_id: Optional[str]) -> Optional[AgentSession]:
        """Load session from persistent storage."""
        if not self.redis_session_store:
            logger.error("Redis session store not initialized")
            return None

        try:
            session = await self.redis_session_store.load_session(session_id)

            if not session:
                return None

            # Verify session belongs to requesting agent when provided
            if agent_id and session.agentId != agent_id:
                logger.warning(
                    "Session %s ownership mismatch: expected %s got %s",
                    session_id,
                    agent_id,
                    session.agentId
                )
                return None

            logger.debug(f"Loaded session {session_id} from Redis storage")
            self._sessions[session_id] = session
            return session

        except Exception as e:
            logger.error(f"Failed to load session {session_id} from storage: {str(e)}")
            return None

    async def _persist_session(self, session: AgentSession):
        """Persist session to storage."""
        if not self.redis_session_store:
            logger.error("Redis session store not initialized")
            return

        try:
            success = await self.redis_session_store.save_session(session)
            if success:
                logger.debug(f"Persisted session {session.id} to Redis storage")
            else:
                logger.error(f"Failed to persist session {session.id} to Redis storage")
        except Exception as e:
            logger.error(f"Error persisting session {session.id}: {str(e)}")

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
