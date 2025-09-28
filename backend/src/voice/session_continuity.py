"""Voice channel session continuity for EFL Agent Assistant."""

import asyncio
import logging
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field

from src.models.agent import ChannelType
from src.models.agent_session import AgentSession, Message, SessionStatus
from src.models.session_context import EntityReference, SessionContext
from src.services.session_service import SessionService
from src.services.response_service import ResponseService
from src.services.track_service import TrackService
from src.voice.voice_response import VoiceResponseFormatter
from src.voice.audio_utils import AudioProcessor
from src.core.config import settings


logger = logging.getLogger(__name__)


@dataclass
class VoiceSessionState:
    """State management for voice sessions."""
    session_id: str
    phone_number: str
    agent_id: str
    current_intent: Optional[str] = None
    conversation_turns: int = 0
    last_activity: datetime = field(default_factory=datetime.utcnow)
    entities_mentioned: List[EntityReference] = field(default_factory=list)
    pending_clarifications: List[str] = field(default_factory=list)
    context_variables: Dict[str, Any] = field(default_factory=dict)
    language: str = field(default_factory=lambda: settings.DEFAULT_LANGUAGE)
    cultural_context: str = field(default_factory=lambda: settings.DEFAULT_CULTURAL_CONTEXT)

    def update_activity(self):
        """Update last activity timestamp."""
        self.last_activity = datetime.utcnow()

    def add_entity(self, entity: EntityReference):
        """Add an entity to the conversation context."""
        # Remove duplicates and maintain order
        existing = [e for e in self.entities_mentioned if e.id != entity.id]
        existing.append(entity)
        self.entities_mentioned = existing[-10:]  # Keep last 10 entities

    def get_relevant_context(self) -> Dict[str, Any]:
        """Get context relevant to current conversation."""
        return {
            "current_intent": self.current_intent,
            "recent_entities": self.entities_mentioned[-3:],  # Last 3 entities
            "conversation_turns": self.conversation_turns,
            "pending_clarifications": self.pending_clarifications,
            "context_variables": self.context_variables,
            "language": self.language,
            "culturalContext": self.cultural_context,
        }


class VoiceContinuityManager:
    """Manages session continuity for voice interactions."""

    def __init__(self):
        self.session_service = None
        self.response_service = None
        self.track_service = None
        self.voice_formatter = None
        self.audio_processor = None
        self.active_voice_sessions: Dict[str, VoiceSessionState] = {}
        self.session_timeout = 1800  # 30 minutes

    async def get_instance(self) -> "VoiceContinuityManager":
        """Get singleton instance with dependencies initialized."""
        if self.session_service is None:
            self.session_service = await SessionService().get_instance()
        if self.response_service is None:
            self.response_service = await ResponseService().get_instance()
        if self.track_service is None:
            self.track_service = await TrackService().get_instance()
        if self.voice_formatter is None:
            self.voice_formatter = await VoiceResponseFormatter().get_instance()
        if self.audio_processor is None:
            self.audio_processor = AudioProcessor()
        return self

    async def handle_voice_interaction(
        self,
        phone_number: str,
        audio_input: bytes,
        session_id: Optional[str] = None,
        *,
        language: Optional[str] = None,
        cultural_context: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Handle a voice interaction with session continuity."""
        try:
            # Get or create session state
            voice_state = await self._get_or_create_voice_state(phone_number, session_id)

            if language:
                voice_state.language = language
            if cultural_context:
                voice_state.cultural_context = cultural_context

            # Process audio input
            processed_audio = self.audio_processor.optimize_for_voice_processing(audio_input)

            # Get or create agent session
            agent_session = await self._ensure_agent_session(voice_state)

            effective_language = (
                language
                or agent_session.context.preferredLanguage
                or voice_state.language
                or settings.DEFAULT_LANGUAGE
            )
            effective_culture = (
                cultural_context
                or agent_session.context.preferredCulturalContext
                or voice_state.cultural_context
                or settings.DEFAULT_CULTURAL_CONTEXT
            )

            voice_state.language = effective_language
            voice_state.cultural_context = effective_culture

            await self.session_service.update_localisation_preferences(
                agent_session.id,
                voice_state.agent_id,
                language=effective_language,
                cultural_context=effective_culture,
            )

            agent_session.context.preferredLanguage = effective_language
            agent_session.context.preferredCulturalContext = effective_culture
            await self.session_service.update_session_context(agent_session.id, agent_session.context)

            # Update activity
            voice_state.update_activity()

            # Extract intent and entities from audio
            intent_info = await self._analyze_intent_and_entities(processed_audio, agent_session)

            # Update session state
            if intent_info['intent']:
                voice_state.current_intent = intent_info['intent']

            for entity in intent_info['entities']:
                voice_state.add_entity(entity)

            # Generate response
            response_data = await self._generate_voice_response(
                agent_session, voice_state, intent_info
            )

            # Update conversation turn count
            voice_state.conversation_turns += 1

            # Store updated state
            self.active_voice_sessions[voice_state.session_id] = voice_state

            return {
                "success": True,
                "session_id": voice_state.session_id,
                "response_text": response_data["text"],
                "audio_response": response_data["audio"],
                "context": voice_state.get_relevant_context(),
                "metadata": {
                    "intent_detected": intent_info['intent'],
                    "entities_found": len(intent_info['entities']),
                    "conversation_turns": voice_state.conversation_turns,
                    "language": voice_state.language,
                    "culturalContext": voice_state.cultural_context,
                }
            }

        except Exception as e:
            logger.error(f"Error handling voice interaction: {e}")
            return {
                "success": False,
                "error": str(e),
                "response_text": "I encountered an error processing your request. Please try again.",
                "audio_response": None
            }

    async def continue_conversation(
        self,
        session_id: str,
        audio_input: bytes,
        context_override: Optional[Dict] = None,
        *,
        language: Optional[str] = None,
        cultural_context: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Continue an existing conversation with context."""
        try:
            voice_state = self.active_voice_sessions.get(session_id)
            if not voice_state:
                return {
                    "success": False,
                    "error": "Session not found",
                    "response_text": "I'm sorry, I don't remember our conversation. Please start over.",
                    "audio_response": None
                }

            # Update context if provided
            if context_override:
                for key, value in context_override.items():
                    if key == "current_intent":
                        voice_state.current_intent = value
                    elif key == "context_variables":
                        voice_state.context_variables.update(value)

            if language:
                voice_state.language = language
            if cultural_context:
                voice_state.cultural_context = cultural_context

            # Process the continuation
            return await self.handle_voice_interaction(
                voice_state.phone_number,
                audio_input,
                session_id,
                language=voice_state.language,
                cultural_context=voice_state.cultural_context,
            )

        except Exception as e:
            logger.error(f"Error continuing conversation: {e}")
            return {
                "success": False,
                "error": str(e),
                "response_text": "I encountered an error continuing our conversation. Please try again.",
                "audio_response": None
            }

    async def sync_from_chat(
        self,
        session_id: str,
        agent_id: str,
        chat_context: SessionContext,
        context_override: Optional[Dict[str, Any]] = None,
    ) -> VoiceSessionState:
        """Hydrate or create voice state using chat context before switching channels."""
        override = context_override or {}
        phone_number = override.get("phone_number") or "unknown"

        voice_state = await self._get_or_create_voice_state(phone_number, session_id)
        voice_state.agent_id = agent_id or voice_state.agent_id

        # Sync intent and entities
        if chat_context.currentIntent:
            voice_state.current_intent = chat_context.currentIntent

        if chat_context.activeEntities:
            voice_state.entities_mentioned = list(chat_context.activeEntities[-10:])

        # Merge pending actions and context variables
        voice_state.pending_clarifications = list(chat_context.pendingActions or [])[-5:]
        voice_state.context_variables.update({
            "last_chat_response": chat_context.lastResponse,
        })

        extra_context = override.get("context_variables")
        if isinstance(extra_context, dict):
            voice_state.context_variables.update(extra_context)

        if override.get("current_intent"):
            voice_state.current_intent = override["current_intent"]

        if chat_context.preferredLanguage:
            voice_state.language = chat_context.preferredLanguage
        if chat_context.preferredCulturalContext:
            voice_state.cultural_context = chat_context.preferredCulturalContext

        override_language = override.get("language")
        override_culture = override.get("cultural_context") or override.get("culturalContext")
        if override_language:
            voice_state.language = override_language
        if override_culture:
            voice_state.cultural_context = override_culture

        voice_state.update_activity()

        agent_session = await self._ensure_agent_session(voice_state)
        agent_session.channel = ChannelType.VOICE
        agent_session.context.preferredChannel = ChannelType.VOICE
        agent_session.context.currentIntent = voice_state.current_intent
        agent_session.context.activeEntities = list(chat_context.activeEntities or [])
        agent_session.context.pendingActions = list(chat_context.pendingActions or [])
        agent_session.context.lastResponse = chat_context.lastResponse
        agent_session.context.preferredLanguage = voice_state.language
        agent_session.context.preferredCulturalContext = voice_state.cultural_context
        await self.session_service.update_session_context(agent_session.id, agent_session.context)
        await self.session_service.update_localisation_preferences(
            agent_session.id,
            voice_state.agent_id,
            language=voice_state.language,
            cultural_context=voice_state.cultural_context,
        )

        return voice_state

    async def get_session_context(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get context for a voice session."""
        voice_state = self.active_voice_sessions.get(session_id)
        if not voice_state:
            return None

        return voice_state.get_relevant_context()

    async def end_voice_session(self, session_id: str) -> bool:
        """End a voice session and clean up state."""
        try:
            if session_id in self.active_voice_sessions:
                del self.active_voice_sessions[session_id]

            # Also end the underlying agent session
            # This would typically be handled by the session service

            logger.info(f"Ended voice session {session_id}")
            return True

        except Exception as e:
            logger.error(f"Error ending voice session {session_id}: {e}")
            return False

    async def _get_or_create_voice_state(
        self,
        phone_number: str,
        session_id: Optional[str] = None
    ) -> VoiceSessionState:
        """Get existing voice state or create new one."""
        if session_id and session_id in self.active_voice_sessions:
            return self.active_voice_sessions[session_id]

        # Create new voice state
        if not session_id:
            session_id = f"voice_{phone_number}_{datetime.utcnow().timestamp()}"

        voice_state = VoiceSessionState(
            session_id=session_id,
            phone_number=phone_number,
            agent_id=phone_number or "voice_user",  # Tie session to caller when available
        )

        self.active_voice_sessions[session_id] = voice_state
        return voice_state

    async def _ensure_agent_session(self, voice_state: VoiceSessionState) -> AgentSession:
        """Ensure an agent session exists for the voice state."""
        # Get existing session or create new one
        agent_session = await self.session_service.get_session(
            voice_state.session_id, voice_state.agent_id
        )

        if not agent_session:
            # Create new session
            agent_session = await self.session_service.create_session(
                voice_state.agent_id, ChannelType.VOICE
            )
            agent_session.id = voice_state.session_id  # Override with voice session ID

        return agent_session

    async def _analyze_intent_and_entities(
        self,
        audio_data: bytes,
        session: AgentSession
    ) -> Dict[str, Any]:
        """Analyze audio to extract intent and entities."""
        try:
            # This would typically use speech recognition and NLP
            # For now, we'll simulate this with simple logic

            # In a real implementation, you would:
            # 1. Transcribe the audio using OpenAI Whisper or similar
            # 2. Use NLP to extract intent and entities
            # 3. Map to your domain model

            # For now, return simulated results
            return {
                "intent": "track_container",
                "entities": [
                    EntityReference(
                        type="container",
                        id="EFLU7896543",
                        confidence=0.95
                    )
                ],
                "confidence": 0.85
            }

        except Exception as e:
            logger.error(f"Error analyzing intent and entities: {e}")
            return {
                "intent": None,
                "entities": [],
                "confidence": 0.0
            }

    async def _generate_voice_response(
        self,
        session: AgentSession,
        voice_state: VoiceSessionState,
        intent_info: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate a voice response based on intent and context."""
        try:
            # Use the track service to get data
            containers, bill_of_ladings = await self.track_service.track_containers(
                intent_info.get('entities', [])
            )

            # Format response for voice
            response_text = self.voice_formatter.format_voice_response(
                query=intent_info.get('intent', 'unknown'),
                containers=containers,
                bill_of_ladings=bill_of_ladings
            )

            # Generate audio response
            audio_response = await self._generate_audio_response(response_text)

            return {
                "text": response_text,
                "audio": audio_response,
                "duration": len(audio_response) / 16000 if audio_response else 0  # Rough duration estimate
            }

        except Exception as e:
            logger.error(f"Error generating voice response: {e}")
            error_text = self.voice_formatter.format_error_voice(str(e))
            error_audio = await self._generate_audio_response(error_text)

            return {
                "text": error_text,
                "audio": error_audio,
                "duration": len(error_audio) / 16000 if error_audio else 0
            }

    async def _generate_audio_response(self, text: str) -> bytes:
        """Generate audio response from text."""
        try:
            # This would use OpenAI TTS or similar service
            # For now, return silence
            return b""
        except Exception as e:
            logger.error(f"Error generating audio response: {e}")
            return b""

    async def cleanup_expired_sessions(self):
        """Clean up expired voice sessions."""
        current_time = datetime.utcnow()
        expired_sessions = []

        for session_id, voice_state in self.active_voice_sessions.items():
            age = (current_time - voice_state.last_activity).total_seconds()
            if age > self.session_timeout:
                expired_sessions.append(session_id)

        for session_id in expired_sessions:
            await self.end_voice_session(session_id)
            logger.info(f"Cleaned up expired voice session {session_id}")

    async def get_session_summary(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get a summary of voice session activity."""
        voice_state = self.active_voice_sessions.get(session_id)
        if not voice_state:
            return None

        return {
            "session_id": voice_state.session_id,
            "phone_number": voice_state.phone_number,
            "current_intent": voice_state.current_intent,
            "conversation_turns": voice_state.conversation_turns,
            "duration": (datetime.utcnow() - voice_state.last_activity).total_seconds(),
            "entities_mentioned": len(voice_state.entities_mentioned),
            "pending_clarifications": len(voice_state.pending_clarifications)
        }

    def get_active_session_count(self) -> int:
        """Get count of active voice sessions."""
        return len(self.active_voice_sessions)


# Global instance
_voice_continuity: Optional[VoiceContinuityManager] = None


async def get_voice_continuity() -> VoiceContinuityManager:
    """Get or create voice continuity manager instance."""
    global _voice_continuity
    if _voice_continuity is None:
        _voice_continuity = await VoiceContinuityManager().get_instance()
    return _voice_continuity
