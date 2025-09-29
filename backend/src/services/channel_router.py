"""Service for multi-channel routing between voice and chat."""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Set, Any

from src.models.agent import ChannelType, AgentSession, SessionStatus, EntityReference
from src.services.session_service import SessionService
from src.voice.session_continuity import get_voice_continuity
from src.chat.chat_continuity import ChatContinuityManager


logger = logging.getLogger(__name__)


class ChannelPreference(str, Enum):
    """Channel preference types."""
    VOICE_PREFERRED = "voice_preferred"
    CHAT_PREFERRED = "chat_preferred"
    NO_PREFERENCE = "no_preference"
    ADAPTIVE = "adaptive"


@dataclass
class ChannelUsageStats:
    """Track channel usage statistics for preference learning."""
    voice_sessions: int = 0
    chat_sessions: int = 0
    voice_duration: float = 0.0
    chat_duration: float = 0.0
    voice_to_chat_switches: int = 0
    chat_to_voice_switches: int = 0
    last_used_channel: Optional[ChannelType] = None
    last_activity: datetime = field(default_factory=datetime.utcnow)


@dataclass
class ActiveChannelSession:
    """Track active sessions per channel."""
    session_id: str
    channel: ChannelType
    agent_id: str
    start_time: datetime = field(default_factory=datetime.utcnow)
    last_activity: datetime = field(default_factory=datetime.utcnow)
    context_hash: str = ""
    
    def update_activity(self):
        """Update last activity timestamp."""
        self.last_activity = datetime.utcnow()


class ChannelRouterService:
    """Route interactions between voice and chat while preserving context."""

    def __init__(self):
        self.session_service: Optional[SessionService] = None
        self.chat_continuity: Optional[ChatContinuityManager] = None
        self.voice_continuity = None
        
        # Multi-channel session management
        self.active_sessions: Dict[str, List[ActiveChannelSession]] = {}
        self.channel_preferences: Dict[str, ChannelPreference] = {}
        self.usage_stats: Dict[str, ChannelUsageStats] = {}
        
        # Context synchronization
        self.context_sync_queue: Dict[str, List[Dict[str, Any]]] = {}
        self.context_locks: Dict[str, asyncio.Lock] = {}

    async def get_instance(self) -> "ChannelRouterService":
        if self.session_service is None:
            self.session_service = await SessionService().get_instance()
        if self.chat_continuity is None:
            self.chat_continuity = await ChatContinuityManager().get_instance()
        if self.voice_continuity is None:
            self.voice_continuity = await get_voice_continuity()
        return self

    async def route_to_voice(
        self, 
        session_id: str, 
        agent_id: str, 
        context_override: Optional[Dict] = None,
        preserve_chat_context: bool = True
    ) -> Dict[str, Any]:
        """Route session to voice channel with seamless context transfer."""
        async with self._get_context_lock(session_id):
            try:
                # Get current session and context
                session = await self.session_service.get_session(session_id, agent_id)
                chat_context = None
                
                if session and preserve_chat_context:
                    # Capture current chat context
                    chat_context = await self._capture_chat_context(session_id, agent_id)
                
                # Create or update voice session
                voice_session = await self._ensure_voice_session(session_id, agent_id)
                
                # Transfer context from chat to voice
                if chat_context:
                    await self._transfer_context_to_voice(session_id, chat_context)
                
                # Apply any context overrides
                if context_override:
                    await self._apply_voice_context_override(session_id, context_override)
                
                # Update session channel
                if session:
                    session.channel = ChannelType.VOICE
                    await self.session_service.update_session_context(session_id, session.context)
                
                # Track the channel switch
                await self._track_channel_switch(agent_id, ChannelType.CHAT, ChannelType.VOICE)
                
                # Register active session
                await self._register_active_session(session_id, agent_id, ChannelType.VOICE)
                
                # Get final voice context
                voice_context = await self.voice_continuity.get_session_context(session_id)
                
                logger.info("Successfully routed session %s to voice channel", session_id)
                
                return {
                    "success": True,
                    "session_id": session_id,
                    "channel": ChannelType.VOICE.value,
                    "context": voice_context or {},
                    "context_preserved": preserve_chat_context and chat_context is not None,
                    "simultaneous_sessions": len(self.active_sessions.get(agent_id, [])) > 1
                }
                
            except Exception as e:
                logger.error(f"Error routing session {session_id} to voice: {e}")
                return {
                    "success": False,
                    "error": str(e),
                    "session_id": session_id,
                    "channel": ChannelType.VOICE.value
                }

    async def route_to_chat(
        self, 
        session_id: str, 
        agent_id: str, 
        voice_context: Optional[Dict] = None,
        preserve_voice_context: bool = True
    ) -> Dict[str, Any]:
        """Route session to chat channel with seamless context transfer."""
        async with self._get_context_lock(session_id):
            try:
                # Get current session
                session = await self.session_service.get_session(session_id, agent_id)
                
                # Capture voice context if needed
                if preserve_voice_context and not voice_context:
                    voice_context = await self._capture_voice_context(session_id)
                
                # Create or update chat session
                chat_session = await self._ensure_chat_session(session_id, agent_id)
                
                # Transfer context from voice to chat
                if voice_context:
                    synced_session = await self.chat_continuity.continue_from_voice(
                        session_id, agent_id, voice_context
                    )
                else:
                    synced_session = chat_session
                
                # Update session channel
                if session:
                    session.channel = ChannelType.CHAT
                    await self.session_service.update_session_context(session_id, session.context)
                
                # Track the channel switch
                await self._track_channel_switch(agent_id, ChannelType.VOICE, ChannelType.CHAT)
                
                # Register active session
                await self._register_active_session(session_id, agent_id, ChannelType.CHAT)
                
                logger.info("Successfully routed session %s to chat channel", session_id)
                
                return {
                    "success": True,
                    "session_id": synced_session.id if synced_session else session_id,
                    "channel": ChannelType.CHAT.value,
                    "context_preserved": preserve_voice_context and voice_context is not None,
                    "simultaneous_sessions": len(self.active_sessions.get(agent_id, [])) > 1
                }
                
            except Exception as e:
                logger.error(f"Error routing session {session_id} to chat: {e}")
                return {
                    "success": False,
                    "error": str(e),
                    "session_id": session_id,
                    "channel": ChannelType.CHAT.value
                }

    async def get_optimal_channel(
        self, 
        agent_id: str, 
        context_hint: Optional[str] = None
    ) -> ChannelType:
        """Determine optimal channel based on preferences and context."""
        try:
            # Get user preference
            preference = self.channel_preferences.get(agent_id, ChannelPreference.NO_PREFERENCE)
            stats = self.usage_stats.get(agent_id, ChannelUsageStats())
            
            # Context-based routing hints
            if context_hint:
                context_lower = context_hint.lower()
                
                # Voice-preferred scenarios
                if any(word in context_lower for word in ["urgent", "quick", "call", "speak"]):
                    return ChannelType.VOICE
                
                # Chat-preferred scenarios  
                if any(word in context_lower for word in ["document", "link", "details", "text"]):
                    return ChannelType.CHAT
            
            # Apply learned preferences
            if preference == ChannelPreference.VOICE_PREFERRED:
                return ChannelType.VOICE
            elif preference == ChannelPreference.CHAT_PREFERRED:
                return ChannelType.CHAT
            elif preference == ChannelPreference.ADAPTIVE:
                # Use most recently used channel
                if stats.last_used_channel:
                    return stats.last_used_channel
            
            # Default based on usage patterns
            if stats.voice_sessions > stats.chat_sessions:
                return ChannelType.VOICE
            elif stats.chat_sessions > stats.voice_sessions:
                return ChannelType.CHAT
            
            # Final fallback
            return ChannelType.CHAT
            
        except Exception as e:
            logger.error(f"Error determining optimal channel for agent {agent_id}: {e}")
            return ChannelType.CHAT

    async def enable_simultaneous_channels(
        self, 
        agent_id: str, 
        primary_session_id: str, 
        secondary_channel: ChannelType
    ) -> Dict[str, Any]:
        """Enable simultaneous multi-channel sessions for the same user."""
        try:
            # Generate new session ID for secondary channel
            secondary_session_id = f"{primary_session_id}_{secondary_channel.value}"
            
            # Get primary session context
            primary_session = await self.session_service.get_session(primary_session_id, agent_id)
            if not primary_session:
                return {
                    "success": False,
                    "error": "Primary session not found"
                }
            
            # Create secondary session with shared context
            if secondary_channel == ChannelType.VOICE:
                result = await self.route_to_voice(
                    secondary_session_id, 
                    agent_id, 
                    preserve_chat_context=True
                )
            else:
                result = await self.route_to_chat(
                    secondary_session_id, 
                    agent_id, 
                    preserve_voice_context=True
                )
            
            if result.get("success"):
                # Set up context synchronization
                await self._setup_context_sync(primary_session_id, secondary_session_id)
                
                logger.info(f"Enabled simultaneous channels for agent {agent_id}")
                
                return {
                    "success": True,
                    "primary_session_id": primary_session_id,
                    "secondary_session_id": secondary_session_id,
                    "secondary_channel": secondary_channel.value,
                    "context_synced": True
                }
            else:
                return result
                
        except Exception as e:
            logger.error(f"Error enabling simultaneous channels for agent {agent_id}: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    async def merge_sessions(
        self, 
        agent_id: str, 
        session_ids: List[str], 
        target_channel: ChannelType
    ) -> Dict[str, Any]:
        """Merge multiple sessions for the same user into a single session."""
        try:
            if len(session_ids) < 2:
                return {
                    "success": False,
                    "error": "At least 2 sessions required for merging"
                }
            
            # Get all sessions
            sessions = []
            for session_id in session_ids:
                session = await self.session_service.get_session(session_id, agent_id)
                if session:
                    sessions.append(session)
            
            if not sessions:
                return {
                    "success": False,
                    "error": "No valid sessions found"
                }
            
            # Use first session as primary
            primary_session = sessions[0]
            merged_session_id = primary_session.id
            
            # Merge contexts and conversation histories
            merged_context = primary_session.context
            merged_history = primary_session.conversationHistory.copy()
            
            for session in sessions[1:]:
                # Merge active entities (deduplicate)
                for entity in session.context.activeEntities:
                    if not any(e.id == entity.id and e.type == entity.type 
                             for e in merged_context.activeEntities):
                        merged_context.activeEntities.append(entity)
                
                # Merge conversation history (chronologically)
                merged_history.extend(session.conversationHistory)
                
                # Update pending actions
                merged_context.pendingActions.extend(session.context.pendingActions)
                
                # End the secondary session
                await self.session_service.end_session(session.id, agent_id)
                await self._unregister_active_session(session.id, agent_id)
            
            # Sort conversation history by timestamp
            merged_history.sort(key=lambda m: m.timestamp)
            
            # Update primary session
            primary_session.conversationHistory = merged_history
            primary_session.context = merged_context
            primary_session.channel = target_channel
            
            # Route to target channel
            if target_channel == ChannelType.VOICE:
                await self.route_to_voice(merged_session_id, agent_id, preserve_chat_context=True)
            else:
                await self.route_to_chat(merged_session_id, agent_id, preserve_voice_context=True)
            
            logger.info(f"Successfully merged {len(session_ids)} sessions for agent {agent_id}")
            
            return {
                "success": True,
                "merged_session_id": merged_session_id,
                "target_channel": target_channel.value,
                "sessions_merged": len(sessions),
                "total_messages": len(merged_history),
                "active_entities": len(merged_context.activeEntities)
            }
            
        except Exception as e:
            logger.error(f"Error merging sessions for agent {agent_id}: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    async def learn_channel_preference(
        self, 
        agent_id: str, 
        channel: ChannelType, 
        session_duration: float, 
        user_satisfaction: Optional[float] = None
    ) -> None:
        """Learn and update channel preferences based on usage patterns."""
        try:
            stats = self.usage_stats.setdefault(agent_id, ChannelUsageStats())
            
            # Update usage statistics
            if channel == ChannelType.VOICE:
                stats.voice_sessions += 1
                stats.voice_duration += session_duration
            else:
                stats.chat_sessions += 1
                stats.chat_duration += session_duration
            
            stats.last_used_channel = channel
            stats.last_activity = datetime.utcnow()
            
            # Analyze patterns and update preferences
            total_sessions = stats.voice_sessions + stats.chat_sessions
            if total_sessions >= 5:  # Minimum sessions for preference learning
                voice_ratio = stats.voice_sessions / total_sessions
                avg_voice_duration = stats.voice_duration / max(stats.voice_sessions, 1)
                avg_chat_duration = stats.chat_duration / max(stats.chat_sessions, 1)
                
                # Determine preference based on usage patterns
                if voice_ratio > 0.7 and avg_voice_duration > avg_chat_duration:
                    self.channel_preferences[agent_id] = ChannelPreference.VOICE_PREFERRED
                elif voice_ratio < 0.3 and avg_chat_duration > avg_voice_duration:
                    self.channel_preferences[agent_id] = ChannelPreference.CHAT_PREFERRED
                else:
                    self.channel_preferences[agent_id] = ChannelPreference.ADAPTIVE
                    
                logger.debug(f"Updated channel preference for agent {agent_id}: {self.channel_preferences[agent_id]}")
                
        except Exception as e:
            logger.error(f"Error learning channel preference for agent {agent_id}: {e}")

    async def get_active_sessions(self, agent_id: str) -> List[Dict[str, Any]]:
        """Get all active sessions for an agent across all channels."""
        try:
            sessions = self.active_sessions.get(agent_id, [])
            return [
                {
                    "session_id": session.session_id,
                    "channel": session.channel.value,
                    "start_time": session.start_time.isoformat(),
                    "last_activity": session.last_activity.isoformat(),
                    "duration": (datetime.utcnow() - session.start_time).total_seconds()
                }
                for session in sessions
            ]
        except Exception as e:
            logger.error(f"Error getting active sessions for agent {agent_id}: {e}")
            return []

    async def cleanup_expired_sessions(self) -> int:
        """Clean up expired sessions across all channels."""
        cleaned_count = 0
        current_time = datetime.utcnow()
        session_timeout = timedelta(minutes=30)
        
        try:
            for agent_id in list(self.active_sessions.keys()):
                sessions = self.active_sessions[agent_id]
                active_sessions = []
                
                for session in sessions:
                    if current_time - session.last_activity > session_timeout:
                        logger.info(f"Cleaning up expired session {session.session_id}")
                        cleaned_count += 1
                    else:
                        active_sessions.append(session)
                
                if active_sessions:
                    self.active_sessions[agent_id] = active_sessions
                else:
                    del self.active_sessions[agent_id]
                    
        except Exception as e:
            logger.error(f"Error cleaning up expired sessions: {e}")
            
        return cleaned_count

    # Helper methods
    
    def _get_context_lock(self, session_id: str) -> asyncio.Lock:
        """Get or create a context lock for a session."""
        if session_id not in self.context_locks:
            self.context_locks[session_id] = asyncio.Lock()
        return self.context_locks[session_id]

    async def _capture_chat_context(self, session_id: str, agent_id: str) -> Optional[Dict[str, Any]]:
        """Capture current chat context for transfer to voice."""
        try:
            context = await self.chat_continuity.hydrate_context(session_id, agent_id)
            if context:
                return {
                    "current_intent": context.currentIntent,
                    "recent_entities": [
                        {
                            "type": entity.type,
                            "id": entity.id,
                            "confidence": entity.confidence
                        }
                        for entity in context.activeEntities[-5:]  # Last 5 entities
                    ],
                    "last_response": context.lastResponse,
                    "pending_clarifications": context.pendingActions,
                    "context_variables": {}
                }
            return None
        except Exception as e:
            logger.error(f"Error capturing chat context for session {session_id}: {e}")
            return None

    async def _capture_voice_context(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Capture current voice context for transfer to chat."""
        try:
            return await self.voice_continuity.get_session_context(session_id)
        except Exception as e:
            logger.error(f"Error capturing voice context for session {session_id}: {e}")
            return None

    async def _ensure_voice_session(self, session_id: str, agent_id: str) -> Optional[Any]:
        """Ensure a voice session exists."""
        try:
            # This would typically interact with the voice continuity manager
            # to ensure a voice session exists for the given session_id
            return await self.voice_continuity.continue_conversation(session_id, b"", {})
        except Exception as e:
            logger.error(f"Error ensuring voice session {session_id}: {e}")
            return None

    async def _ensure_chat_session(self, session_id: str, agent_id: str) -> Optional[Any]:
        """Ensure a chat session exists."""
        try:
            session = await self.session_service.get_session(session_id, agent_id)
            if not session:
                session = await self.session_service.create_session(agent_id, ChannelType.CHAT)
                session.id = session_id
            return session
        except Exception as e:
            logger.error(f"Error ensuring chat session {session_id}: {e}")
            return None

    async def _transfer_context_to_voice(self, session_id: str, chat_context: Dict[str, Any]) -> None:
        """Transfer context from chat to voice channel."""
        try:
            # Convert chat context to voice-compatible format
            voice_context_override = {
                "current_intent": chat_context.get("current_intent"),
                "context_variables": {
                    "entities": chat_context.get("recent_entities", []),
                    "last_response": chat_context.get("last_response", ""),
                    "pending_actions": chat_context.get("pending_clarifications", [])
                }
            }
            
            # Apply to voice session
            await self.voice_continuity.continue_conversation(
                session_id, b"", voice_context_override
            )
            
        except Exception as e:
            logger.error(f"Error transferring context to voice for session {session_id}: {e}")

    async def _apply_voice_context_override(self, session_id: str, context_override: Dict[str, Any]) -> None:
        """Apply context override to voice session."""
        try:
            await self.voice_continuity.continue_conversation(
                session_id, b"", context_override
            )
        except Exception as e:
            logger.error(f"Error applying voice context override for session {session_id}: {e}")

    async def _track_channel_switch(
        self, 
        agent_id: str, 
        from_channel: ChannelType, 
        to_channel: ChannelType
    ) -> None:
        """Track channel switching for preference learning."""
        try:
            stats = self.usage_stats.setdefault(agent_id, ChannelUsageStats())
            
            if from_channel == ChannelType.VOICE and to_channel == ChannelType.CHAT:
                stats.voice_to_chat_switches += 1
            elif from_channel == ChannelType.CHAT and to_channel == ChannelType.VOICE:
                stats.chat_to_voice_switches += 1
                
            stats.last_used_channel = to_channel
            stats.last_activity = datetime.utcnow()
            
        except Exception as e:
            logger.error(f"Error tracking channel switch for agent {agent_id}: {e}")

    async def _register_active_session(
        self, 
        session_id: str, 
        agent_id: str, 
        channel: ChannelType
    ) -> None:
        """Register an active session for tracking."""
        try:
            sessions = self.active_sessions.setdefault(agent_id, [])
            
            # Remove existing session with same ID
            sessions = [s for s in sessions if s.session_id != session_id]
            
            # Add new session
            active_session = ActiveChannelSession(
                session_id=session_id,
                channel=channel,
                agent_id=agent_id
            )
            sessions.append(active_session)
            
            self.active_sessions[agent_id] = sessions
            
        except Exception as e:
            logger.error(f"Error registering active session {session_id}: {e}")

    async def _unregister_active_session(self, session_id: str, agent_id: str) -> None:
        """Unregister an active session."""
        try:
            if agent_id in self.active_sessions:
                sessions = self.active_sessions[agent_id]
                sessions = [s for s in sessions if s.session_id != session_id]
                
                if sessions:
                    self.active_sessions[agent_id] = sessions
                else:
                    del self.active_sessions[agent_id]
                    
        except Exception as e:
            logger.error(f"Error unregistering active session {session_id}: {e}")

    async def _setup_context_sync(self, primary_session_id: str, secondary_session_id: str) -> None:
        """Set up context synchronization between two sessions."""
        try:
            # Initialize sync queues for both sessions
            self.context_sync_queue[primary_session_id] = []
            self.context_sync_queue[secondary_session_id] = []
            
            logger.debug(f"Set up context sync between {primary_session_id} and {secondary_session_id}")
            
        except Exception as e:
            logger.error(f"Error setting up context sync: {e}")

    async def _sync_context_between_sessions(
        self, 
        source_session_id: str, 
        target_session_id: str, 
        context_update: Dict[str, Any]
    ) -> None:
        """Synchronize context between two active sessions."""
        try:
            # Add context update to sync queue
            if target_session_id in self.context_sync_queue:
                self.context_sync_queue[target_session_id].append({
                    "source": source_session_id,
                    "update": context_update,
                    "timestamp": datetime.utcnow()
                })
                
                # Process sync queue (limit to last 10 updates)
                self.context_sync_queue[target_session_id] = \
                    self.context_sync_queue[target_session_id][-10:]
                    
        except Exception as e:
            logger.error(f"Error syncing context between sessions: {e}")


__all__ = ["ChannelRouterService"]

