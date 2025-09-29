"""Service for multi-channel routing between voice and chat."""

from __future__ import annotations

import logging
from typing import Dict, Optional, List, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field

from src.models.agent import ChannelType, Agent, AgentSession
from src.services.session_service import SessionService
from src.voice.session_continuity import get_voice_continuity
from src.chat.chat_continuity import ChatContinuityManager


logger = logging.getLogger(__name__)


@dataclass
class ChannelPreference:
    """Channel preference data."""
    agent_id: str
    preferred_channel: ChannelType
    context: Optional[str] = None
    confidence: float = 0.5
    learned_from_behavior: bool = False
    last_updated: datetime = field(default_factory=datetime.utcnow)
    usage_count: int = 0


@dataclass
class ConcurrentSession:
    """Tracks concurrent sessions across channels."""
    agent_id: str
    sessions: Dict[ChannelType, str] = field(default_factory=dict)  # channel -> session_id
    primary_channel: Optional[ChannelType] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_activity: datetime = field(default_factory=datetime.utcnow)


class ChannelRouterService:
    """Route interactions between voice and chat while preserving context."""

    def __init__(self):
        self.session_service: Optional[SessionService] = None
        self.chat_continuity: Optional[ChatContinuityManager] = None
        self.channel_preferences: Dict[str, ChannelPreference] = {}
        self.concurrent_sessions: Dict[str, ConcurrentSession] = {}
        self.preference_learning_enabled = True

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

    async def create_concurrent_session(
        self, agent_id: str, primary_channel: ChannelType, secondary_channel: ChannelType
    ) -> Tuple[str, str]:
        """Create concurrent sessions across two channels for the same agent."""
        try:
            # Create sessions for both channels
            primary_session = await self.session_service.create_session(agent_id, primary_channel)
            secondary_session = await self.session_service.create_session(agent_id, secondary_channel)

            # Track concurrent sessions
            concurrent_session = ConcurrentSession(
                agent_id=agent_id,
                sessions={
                    primary_channel: primary_session.id,
                    secondary_channel: secondary_session.id
                },
                primary_channel=primary_channel
            )

            self.concurrent_sessions[agent_id] = concurrent_session
            
            logger.info(f"Created concurrent sessions for agent {agent_id}: {primary_channel.value} (primary), {secondary_channel.value}")
            
            return primary_session.id, secondary_session.id

        except Exception as e:
            logger.error(f"Error creating concurrent sessions for agent {agent_id}: {e}")
            raise

    async def sync_concurrent_sessions(self, agent_id: str) -> bool:
        """Synchronize context between concurrent sessions."""
        try:
            concurrent_session = self.concurrent_sessions.get(agent_id)
            if not concurrent_session:
                return False

            sessions = {}
            for channel, session_id in concurrent_session.sessions.items():
                session = await self.session_service.get_session(session_id, agent_id)
                if session:
                    sessions[channel] = session

            if len(sessions) < 2:
                return False

            # Sync context from primary to secondary sessions
            primary_session = sessions.get(concurrent_session.primary_channel)
            if not primary_session:
                return False

            for channel, session in sessions.items():
                if channel != concurrent_session.primary_channel:
                    # Merge contexts
                    merged_context = self._merge_session_contexts(primary_session.context, session.context)
                    await self.session_service.update_session_context(session.id, merged_context)

            concurrent_session.last_activity = datetime.utcnow()
            logger.info(f"Synchronized concurrent sessions for agent {agent_id}")
            return True

        except Exception as e:
            logger.error(f"Error synchronizing concurrent sessions for agent {agent_id}: {e}")
            return False

    async def detect_preferred_channel(
        self, agent_id: str, intent: Optional[str] = None, context: Optional[str] = None
    ) -> ChannelType:
        """Detect preferred channel for an agent based on learned behavior."""
        try:
            # Check for specific context preferences
            context_key = f"{agent_id}:{context}" if context else agent_id
            preference = self.channel_preferences.get(context_key)

            if preference and preference.confidence > 0.7:
                logger.debug(f"Using learned preference for agent {agent_id}: {preference.preferred_channel.value}")
                return preference.preferred_channel

            # Fallback to intent-based detection
            if intent:
                if intent in ["track_container", "urgent_inquiry"]:
                    return ChannelType.VOICE  # Quick queries prefer voice
                elif intent in ["complex_query", "documentation_request"]:
                    return ChannelType.CHAT  # Complex queries prefer chat

            # Default fallback
            return ChannelType.CHAT

        except Exception as e:
            logger.error(f"Error detecting preferred channel for agent {agent_id}: {e}")
            return ChannelType.CHAT

    async def learn_channel_preference(
        self, agent_id: str, chosen_channel: ChannelType, intent: Optional[str] = None, context: Optional[str] = None
    ) -> None:
        """Learn and update channel preferences based on user behavior."""
        if not self.preference_learning_enabled:
            return

        try:
            context_key = f"{agent_id}:{context}" if context else agent_id
            
            existing_preference = self.channel_preferences.get(context_key)
            
            if existing_preference:
                # Update existing preference
                if existing_preference.preferred_channel == chosen_channel:
                    existing_preference.confidence = min(1.0, existing_preference.confidence + 0.1)
                else:
                    existing_preference.confidence = max(0.0, existing_preference.confidence - 0.05)
                    if existing_preference.confidence < 0.3:
                        existing_preference.preferred_channel = chosen_channel
                        existing_preference.confidence = 0.5
                
                existing_preference.usage_count += 1
                existing_preference.last_updated = datetime.utcnow()
                existing_preference.learned_from_behavior = True
            else:
                # Create new preference
                new_preference = ChannelPreference(
                    agent_id=agent_id,
                    preferred_channel=chosen_channel,
                    context=context,
                    confidence=0.6,
                    learned_from_behavior=True,
                    usage_count=1
                )
                self.channel_preferences[context_key] = new_preference

            logger.debug(f"Updated channel preference for agent {agent_id} (context: {context}): {chosen_channel.value}")

        except Exception as e:
            logger.error(f"Error learning channel preference for agent {agent_id}: {e}")

    async def get_agent_concurrent_sessions(self, agent_id: str) -> Optional[ConcurrentSession]:
        """Get concurrent sessions for an agent."""
        return self.concurrent_sessions.get(agent_id)

    async def end_concurrent_sessions(self, agent_id: str) -> bool:
        """End all concurrent sessions for an agent."""
        try:
            concurrent_session = self.concurrent_sessions.get(agent_id)
            if not concurrent_session:
                return False

            # End all sessions
            for channel, session_id in concurrent_session.sessions.items():
                await self.session_service.end_session(session_id, agent_id)

            # Remove from tracking
            del self.concurrent_sessions[agent_id]
            
            logger.info(f"Ended concurrent sessions for agent {agent_id}")
            return True

        except Exception as e:
            logger.error(f"Error ending concurrent sessions for agent {agent_id}: {e}")
            return False

    def _merge_session_contexts(self, primary_context, secondary_context):
        """Merge two session contexts intelligently."""
        from src.models.agent import SessionContext

        # Create merged context prioritizing primary
        merged_context = SessionContext(
            currentIntent=primary_context.currentIntent or secondary_context.currentIntent,
            activeEntities=primary_context.activeEntities.copy(),
            lastResponse=primary_context.lastResponse or secondary_context.lastResponse,
            pendingActions=primary_context.pendingActions.copy()
        )

        # Add unique entities from secondary context
        primary_entity_ids = {(e.type, e.id) for e in primary_context.activeEntities}
        for entity in secondary_context.activeEntities:
            entity_key = (entity.type, entity.id)
            if entity_key not in primary_entity_ids:
                merged_context.activeEntities.append(entity)

        # Limit to last 10 entities
        merged_context.activeEntities = merged_context.activeEntities[-10:]

        # Merge pending actions (remove duplicates)
        for action in secondary_context.pendingActions:
            if action not in merged_context.pendingActions:
                merged_context.pendingActions.append(action)

        return merged_context

    async def cleanup_expired_concurrent_sessions(self) -> None:
        """Clean up expired concurrent sessions."""
        current_time = datetime.utcnow()
        timeout_threshold = timedelta(hours=1)  # 1 hour timeout
        
        expired_agents = []
        for agent_id, concurrent_session in self.concurrent_sessions.items():
            if current_time - concurrent_session.last_activity > timeout_threshold:
                expired_agents.append(agent_id)

        for agent_id in expired_agents:
            await self.end_concurrent_sessions(agent_id)
            logger.info(f"Cleaned up expired concurrent sessions for agent {agent_id}")

    def get_channel_routing_stats(self) -> Dict[str, any]:
        """Get statistics about channel routing."""
        total_preferences = len(self.channel_preferences)
        voice_preferences = sum(1 for p in self.channel_preferences.values() if p.preferred_channel == ChannelType.VOICE)
        chat_preferences = sum(1 for p in self.channel_preferences.values() if p.preferred_channel == ChannelType.CHAT)
        
        return {
            "total_preferences": total_preferences,
            "voice_preferences": voice_preferences,
            "chat_preferences": chat_preferences,
            "concurrent_sessions": len(self.concurrent_sessions),
            "learning_enabled": self.preference_learning_enabled
        }


__all__ = ["ChannelRouterService", "ChannelPreference", "ConcurrentSession"]

