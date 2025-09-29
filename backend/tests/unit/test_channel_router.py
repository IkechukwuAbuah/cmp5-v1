"""Unit tests for ChannelRouterService."""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch

from src.services.channel_router import ChannelRouterService, ChannelPreference, ConcurrentSession
from src.models.agent import ChannelType, AgentSession, SessionContext, SessionStatus, EntityReference, Message


class TestChannelRouterService:
    """Test cases for ChannelRouterService."""

    @pytest.fixture
    async def channel_router(self):
        """Create a ChannelRouterService instance for testing."""
        service = ChannelRouterService()
        service.session_service = AsyncMock()
        service.chat_continuity = AsyncMock()
        return service

    @pytest.fixture
    def sample_session(self):
        """Create a sample AgentSession for testing."""
        return AgentSession(
            id="test_session_123",
            agentId="agent_123",
            channel=ChannelType.CHAT,
            startTime=datetime.utcnow(),
            status=SessionStatus.ACTIVE,
            context=SessionContext(
                currentIntent="track_container",
                activeEntities=[
                    EntityReference(type="container", id="EFLU1234567", confidence=0.95)
                ],
                lastResponse="I can help you track that container.",
                pendingActions=[]
            )
        )

    async def test_route_to_voice(self, channel_router, sample_session):
        """Test routing session to voice channel."""
        # Mock dependencies
        channel_router.session_service.get_session.return_value = sample_session
        channel_router.session_service.update_session_context.return_value = True

        # Mock voice continuity
        with patch('src.services.channel_router.get_voice_continuity') as mock_voice:
            mock_voice_continuity = AsyncMock()
            mock_voice_continuity.get_session_context.return_value = {
                "current_intent": "track_container",
                "recent_entities": [{"type": "container", "id": "EFLU1234567"}]
            }
            mock_voice.return_value = mock_voice_continuity

            result = await channel_router.route_to_voice("test_session_123", "agent_123")

            assert result is not None
            assert "current_intent" in result
            mock_voice_continuity.get_session_context.assert_called_once_with("test_session_123")

    async def test_route_to_chat(self, channel_router, sample_session):
        """Test routing session to chat channel."""
        # Mock dependencies
        channel_router.session_service.get_session.return_value = sample_session
        channel_router.session_service.update_session_context.return_value = True
        
        mock_synced_session = Mock()
        mock_synced_session.id = "synced_session_123"
        channel_router.chat_continuity.continue_from_voice.return_value = mock_synced_session

        voice_context = {
            "current_intent": "track_container",
            "recent_entities": [{"type": "container", "id": "EFLU1234567"}]
        }

        result = await channel_router.route_to_chat("test_session_123", "agent_123", voice_context)

        assert result["sessionId"] == "synced_session_123"
        assert result["channel"] == ChannelType.CHAT.value
        channel_router.chat_continuity.continue_from_voice.assert_called_once()

    async def test_create_concurrent_session(self, channel_router):
        """Test creating concurrent sessions across channels."""
        # Mock session creation
        voice_session = Mock()
        voice_session.id = "voice_session_123"
        chat_session = Mock()
        chat_session.id = "chat_session_123"

        channel_router.session_service.create_session.side_effect = [voice_session, chat_session]

        primary_id, secondary_id = await channel_router.create_concurrent_session(
            "agent_123", ChannelType.VOICE, ChannelType.CHAT
        )

        assert primary_id == "voice_session_123"
        assert secondary_id == "chat_session_123"
        assert "agent_123" in channel_router.concurrent_sessions
        
        concurrent_session = channel_router.concurrent_sessions["agent_123"]
        assert concurrent_session.primary_channel == ChannelType.VOICE
        assert len(concurrent_session.sessions) == 2

    async def test_sync_concurrent_sessions(self, channel_router, sample_session):
        """Test synchronizing context between concurrent sessions."""
        # Setup concurrent session
        concurrent_session = ConcurrentSession(
            agent_id="agent_123",
            sessions={
                ChannelType.VOICE: "voice_session_123",
                ChannelType.CHAT: "chat_session_123"
            },
            primary_channel=ChannelType.VOICE
        )
        channel_router.concurrent_sessions["agent_123"] = concurrent_session

        # Mock session retrieval
        voice_session = sample_session
        voice_session.channel = ChannelType.VOICE
        chat_session = sample_session
        chat_session.channel = ChannelType.CHAT
        chat_session.id = "chat_session_123"

        channel_router.session_service.get_session.side_effect = [voice_session, chat_session]
        channel_router.session_service.update_session_context.return_value = True

        result = await channel_router.sync_concurrent_sessions("agent_123")

        assert result is True
        channel_router.session_service.update_session_context.assert_called()

    async def test_detect_preferred_channel_learned(self, channel_router):
        """Test channel preference detection with learned preferences."""
        # Setup learned preference
        preference = ChannelPreference(
            agent_id="agent_123",
            preferred_channel=ChannelType.VOICE,
            context="urgent",
            confidence=0.8,
            learned_from_behavior=True
        )
        channel_router.channel_preferences["agent_123:urgent"] = preference

        result = await channel_router.detect_preferred_channel("agent_123", context="urgent")

        assert result == ChannelType.VOICE

    async def test_detect_preferred_channel_intent_based(self, channel_router):
        """Test channel preference detection based on intent."""
        result = await channel_router.detect_preferred_channel("agent_123", intent="track_container")
        assert result == ChannelType.VOICE

        result = await channel_router.detect_preferred_channel("agent_123", intent="complex_query")
        assert result == ChannelType.CHAT

    async def test_learn_channel_preference_new(self, channel_router):
        """Test learning new channel preference."""
        await channel_router.learn_channel_preference(
            "agent_123", ChannelType.VOICE, intent="track_container", context="urgent"
        )

        preference_key = "agent_123:urgent"
        assert preference_key in channel_router.channel_preferences
        
        preference = channel_router.channel_preferences[preference_key]
        assert preference.preferred_channel == ChannelType.VOICE
        assert preference.confidence == 0.6
        assert preference.learned_from_behavior is True

    async def test_learn_channel_preference_update_existing(self, channel_router):
        """Test updating existing channel preference."""
        # Setup existing preference
        preference = ChannelPreference(
            agent_id="agent_123",
            preferred_channel=ChannelType.VOICE,
            confidence=0.5,
            usage_count=1
        )
        channel_router.channel_preferences["agent_123"] = preference

        # Learn same preference (should increase confidence)
        await channel_router.learn_channel_preference("agent_123", ChannelType.VOICE)

        updated_preference = channel_router.channel_preferences["agent_123"]
        assert updated_preference.confidence == 0.6  # 0.5 + 0.1
        assert updated_preference.usage_count == 2

    async def test_learn_channel_preference_conflicting(self, channel_router):
        """Test learning conflicting channel preference."""
        # Setup existing preference
        preference = ChannelPreference(
            agent_id="agent_123",
            preferred_channel=ChannelType.VOICE,
            confidence=0.5,
            usage_count=1
        )
        channel_router.channel_preferences["agent_123"] = preference

        # Learn different preference (should decrease confidence)
        await channel_router.learn_channel_preference("agent_123", ChannelType.CHAT)

        updated_preference = channel_router.channel_preferences["agent_123"]
        assert updated_preference.confidence == 0.45  # 0.5 - 0.05

    async def test_end_concurrent_sessions(self, channel_router):
        """Test ending concurrent sessions."""
        # Setup concurrent session
        concurrent_session = ConcurrentSession(
            agent_id="agent_123",
            sessions={
                ChannelType.VOICE: "voice_session_123",
                ChannelType.CHAT: "chat_session_123"
            }
        )
        channel_router.concurrent_sessions["agent_123"] = concurrent_session

        channel_router.session_service.end_session.return_value = True

        result = await channel_router.end_concurrent_sessions("agent_123")

        assert result is True
        assert "agent_123" not in channel_router.concurrent_sessions
        assert channel_router.session_service.end_session.call_count == 2

    def test_merge_session_contexts(self, channel_router):
        """Test merging session contexts."""
        primary_context = SessionContext(
            currentIntent="track_container",
            activeEntities=[
                EntityReference(type="container", id="EFLU1234567", confidence=0.95)
            ],
            lastResponse="Primary response",
            pendingActions=["action1"]
        )

        secondary_context = SessionContext(
            currentIntent="get_help",
            activeEntities=[
                EntityReference(type="container", id="EFLU7654321", confidence=0.90),
                EntityReference(type="container", id="EFLU1234567", confidence=0.95)  # Duplicate
            ],
            lastResponse="Secondary response",
            pendingActions=["action2", "action1"]  # One duplicate
        )

        merged_context = channel_router._merge_session_contexts(primary_context, secondary_context)

        assert merged_context.currentIntent == "track_container"  # Primary takes precedence
        assert merged_context.lastResponse == "Primary response"
        assert len(merged_context.activeEntities) == 2  # No duplicates
        assert len(merged_context.pendingActions) == 2  # No duplicates

    async def test_cleanup_expired_concurrent_sessions(self, channel_router):
        """Test cleaning up expired concurrent sessions."""
        # Setup expired session
        expired_session = ConcurrentSession(
            agent_id="agent_expired",
            last_activity=datetime.utcnow() - timedelta(hours=2)  # 2 hours ago
        )
        channel_router.concurrent_sessions["agent_expired"] = expired_session

        # Setup active session
        active_session = ConcurrentSession(
            agent_id="agent_active",
            last_activity=datetime.utcnow() - timedelta(minutes=30)  # 30 minutes ago
        )
        channel_router.concurrent_sessions["agent_active"] = active_session

        channel_router.session_service.end_session.return_value = True

        await channel_router.cleanup_expired_concurrent_sessions()

        # Expired session should be removed
        assert "agent_expired" not in channel_router.concurrent_sessions
        # Active session should remain
        assert "agent_active" in channel_router.concurrent_sessions

    def test_get_channel_routing_stats(self, channel_router):
        """Test getting channel routing statistics."""
        # Setup test data
        channel_router.channel_preferences = {
            "agent1": ChannelPreference("agent1", ChannelType.VOICE),
            "agent2": ChannelPreference("agent2", ChannelType.CHAT),
            "agent3": ChannelPreference("agent3", ChannelType.VOICE)
        }
        channel_router.concurrent_sessions = {
            "agent1": ConcurrentSession("agent1"),
            "agent2": ConcurrentSession("agent2")
        }

        stats = channel_router.get_channel_routing_stats()

        assert stats["total_preferences"] == 3
        assert stats["voice_preferences"] == 2
        assert stats["chat_preferences"] == 1
        assert stats["concurrent_sessions"] == 2
        assert stats["learning_enabled"] is True

    async def test_get_agent_concurrent_sessions(self, channel_router):
        """Test getting concurrent sessions for an agent."""
        concurrent_session = ConcurrentSession(agent_id="agent_123")
        channel_router.concurrent_sessions["agent_123"] = concurrent_session

        result = await channel_router.get_agent_concurrent_sessions("agent_123")

        assert result is not None
        assert result.agent_id == "agent_123"

        # Test non-existent agent
        result = await channel_router.get_agent_concurrent_sessions("nonexistent")
        assert result is None