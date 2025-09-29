"""Unit tests for ChannelRouterService."""

import asyncio
import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

from src.models.agent import ChannelType, AgentSession, SessionStatus, SessionContext, EntityReference
from src.services.channel_router import (
    ChannelRouterService, 
    ChannelPreference, 
    ChannelUsageStats,
    ActiveChannelSession
)


class TestChannelRouterService:
    """Test cases for ChannelRouterService."""

    @pytest.fixture
    async def router_service(self):
        """Create a ChannelRouterService instance for testing."""
        service = ChannelRouterService()
        
        # Mock dependencies
        service.session_service = AsyncMock()
        service.chat_continuity = AsyncMock()
        service.voice_continuity = AsyncMock()
        
        return service

    @pytest.fixture
    def sample_session(self):
        """Create a sample agent session for testing."""
        return AgentSession(
            id="test_session_123",
            agentId="agent_456",
            channel=ChannelType.CHAT,
            startTime=datetime.utcnow(),
            status=SessionStatus.ACTIVE,
            context=SessionContext(
                currentIntent="track_container",
                activeEntities=[
                    EntityReference(type="container", id="EFLU1234567", confidence=0.95)
                ],
                lastResponse="I found container EFLU1234567",
                pendingActions=["clarify_location"]
            ),
            conversationHistory=[]
        )

    @pytest.fixture
    def sample_chat_context(self):
        """Create sample chat context for testing."""
        return {
            "current_intent": "track_container",
            "recent_entities": [
                {"type": "container", "id": "EFLU1234567", "confidence": 0.95}
            ],
            "last_response": "I found container EFLU1234567",
            "pending_clarifications": ["clarify_location"],
            "context_variables": {}
        }

    @pytest.fixture
    def sample_voice_context(self):
        """Create sample voice context for testing."""
        return {
            "current_intent": "track_container",
            "recent_entities": [
                {"type": "container", "id": "EFLU1234567", "confidence": 0.95}
            ],
            "conversation_turns": 3,
            "pending_clarifications": ["clarify_location"],
            "context_variables": {"last_audio_duration": 15.2}
        }

    async def test_get_instance(self, router_service):
        """Test service instance creation."""
        instance = await router_service.get_instance()
        assert instance is not None
        assert instance.session_service is not None
        assert instance.chat_continuity is not None
        assert instance.voice_continuity is not None

    async def test_route_to_voice_success(self, router_service, sample_session, sample_chat_context):
        """Test successful routing to voice channel."""
        # Setup mocks
        router_service.session_service.get_session.return_value = sample_session
        router_service._capture_chat_context = AsyncMock(return_value=sample_chat_context)
        router_service._ensure_voice_session = AsyncMock(return_value=True)
        router_service._transfer_context_to_voice = AsyncMock()
        router_service._track_channel_switch = AsyncMock()
        router_service._register_active_session = AsyncMock()
        router_service.voice_continuity.get_session_context.return_value = {"voice_context": True}
        
        # Execute
        result = await router_service.route_to_voice("test_session_123", "agent_456")
        
        # Verify
        assert result["success"] is True
        assert result["session_id"] == "test_session_123"
        assert result["channel"] == ChannelType.VOICE.value
        assert result["context_preserved"] is True
        assert "context" in result
        
        # Verify method calls
        router_service._capture_chat_context.assert_called_once_with("test_session_123", "agent_456")
        router_service._transfer_context_to_voice.assert_called_once()
        router_service._track_channel_switch.assert_called_once()

    async def test_route_to_voice_error_handling(self, router_service):
        """Test error handling in route_to_voice."""
        # Setup mock to raise exception
        router_service.session_service.get_session.side_effect = Exception("Database error")
        
        # Execute
        result = await router_service.route_to_voice("test_session_123", "agent_456")
        
        # Verify error response
        assert result["success"] is False
        assert "error" in result
        assert result["session_id"] == "test_session_123"
        assert result["channel"] == ChannelType.VOICE.value

    async def test_route_to_chat_success(self, router_service, sample_session, sample_voice_context):
        """Test successful routing to chat channel."""
        # Setup mocks
        router_service.session_service.get_session.return_value = sample_session
        router_service._capture_voice_context = AsyncMock(return_value=sample_voice_context)
        router_service._ensure_chat_session = AsyncMock(return_value=sample_session)
        router_service.chat_continuity.continue_from_voice.return_value = sample_session
        router_service._track_channel_switch = AsyncMock()
        router_service._register_active_session = AsyncMock()
        
        # Execute
        result = await router_service.route_to_chat("test_session_123", "agent_456")
        
        # Verify
        assert result["success"] is True
        assert result["session_id"] == "test_session_123"
        assert result["channel"] == ChannelType.CHAT.value
        assert result["context_preserved"] is True
        
        # Verify method calls
        router_service._capture_voice_context.assert_called_once()
        router_service.chat_continuity.continue_from_voice.assert_called_once()

    async def test_route_to_chat_with_provided_context(self, router_service, sample_session, sample_voice_context):
        """Test routing to chat with pre-provided voice context."""
        # Setup mocks
        router_service.session_service.get_session.return_value = sample_session
        router_service._ensure_chat_session = AsyncMock(return_value=sample_session)
        router_service.chat_continuity.continue_from_voice.return_value = sample_session
        router_service._track_channel_switch = AsyncMock()
        router_service._register_active_session = AsyncMock()
        
        # Execute with provided context
        result = await router_service.route_to_chat(
            "test_session_123", 
            "agent_456", 
            voice_context=sample_voice_context
        )
        
        # Verify
        assert result["success"] is True
        assert result["context_preserved"] is True
        
        # Verify context was used directly
        router_service.chat_continuity.continue_from_voice.assert_called_once_with(
            "test_session_123", "agent_456", sample_voice_context
        )

    async def test_get_optimal_channel_voice_preferred(self, router_service):
        """Test optimal channel selection for voice-preferred user."""
        router_service.channel_preferences["agent_456"] = ChannelPreference.VOICE_PREFERRED
        
        result = await router_service.get_optimal_channel("agent_456")
        assert result == ChannelType.VOICE

    async def test_get_optimal_channel_chat_preferred(self, router_service):
        """Test optimal channel selection for chat-preferred user."""
        router_service.channel_preferences["agent_456"] = ChannelPreference.CHAT_PREFERRED
        
        result = await router_service.get_optimal_channel("agent_456")
        assert result == ChannelType.CHAT

    async def test_get_optimal_channel_context_hints(self, router_service):
        """Test optimal channel selection based on context hints."""
        # Test urgent context -> voice
        result = await router_service.get_optimal_channel("agent_456", "urgent container status")
        assert result == ChannelType.VOICE
        
        # Test document context -> chat
        result = await router_service.get_optimal_channel("agent_456", "need document details")
        assert result == ChannelType.CHAT

    async def test_get_optimal_channel_adaptive_preference(self, router_service):
        """Test adaptive channel preference."""
        router_service.channel_preferences["agent_456"] = ChannelPreference.ADAPTIVE
        stats = ChannelUsageStats(last_used_channel=ChannelType.VOICE)
        router_service.usage_stats["agent_456"] = stats
        
        result = await router_service.get_optimal_channel("agent_456")
        assert result == ChannelType.VOICE

    async def test_get_optimal_channel_usage_patterns(self, router_service):
        """Test channel selection based on usage patterns."""
        stats = ChannelUsageStats(voice_sessions=8, chat_sessions=2)
        router_service.usage_stats["agent_456"] = stats
        
        result = await router_service.get_optimal_channel("agent_456")
        assert result == ChannelType.VOICE

    async def test_enable_simultaneous_channels_success(self, router_service, sample_session):
        """Test enabling simultaneous channels."""
        # Setup mocks
        router_service.session_service.get_session.return_value = sample_session
        router_service.route_to_voice = AsyncMock(return_value={"success": True})
        router_service._setup_context_sync = AsyncMock()
        
        # Execute
        result = await router_service.enable_simultaneous_channels(
            "agent_456", 
            "primary_session", 
            ChannelType.VOICE
        )
        
        # Verify
        assert result["success"] is True
        assert result["primary_session_id"] == "primary_session"
        assert "secondary_session_id" in result
        assert result["secondary_channel"] == ChannelType.VOICE.value
        assert result["context_synced"] is True
        
        # Verify setup was called
        router_service._setup_context_sync.assert_called_once()

    async def test_enable_simultaneous_channels_primary_not_found(self, router_service):
        """Test simultaneous channels when primary session not found."""
        router_service.session_service.get_session.return_value = None
        
        result = await router_service.enable_simultaneous_channels(
            "agent_456", 
            "nonexistent_session", 
            ChannelType.VOICE
        )
        
        assert result["success"] is False
        assert "Primary session not found" in result["error"]

    async def test_merge_sessions_success(self, router_service):
        """Test successful session merging."""
        # Create test sessions
        session1 = AgentSession(
            id="session_1",
            agentId="agent_456",
            channel=ChannelType.CHAT,
            startTime=datetime.utcnow(),
            status=SessionStatus.ACTIVE,
            context=SessionContext(
                currentIntent="track_container",
                activeEntities=[EntityReference(type="container", id="EFLU1111111", confidence=0.95)],
                lastResponse="Found container 1",
                pendingActions=["action1"]
            ),
            conversationHistory=[]
        )
        
        session2 = AgentSession(
            id="session_2",
            agentId="agent_456",
            channel=ChannelType.VOICE,
            startTime=datetime.utcnow(),
            status=SessionStatus.ACTIVE,
            context=SessionContext(
                currentIntent="track_container",
                activeEntities=[EntityReference(type="container", id="EFLU2222222", confidence=0.95)],
                lastResponse="Found container 2",
                pendingActions=["action2"]
            ),
            conversationHistory=[]
        )
        
        # Setup mocks
        router_service.session_service.get_session.side_effect = [session1, session2]
        router_service.session_service.end_session = AsyncMock(return_value=True)
        router_service._unregister_active_session = AsyncMock()
        router_service.route_to_chat = AsyncMock()
        
        # Execute
        result = await router_service.merge_sessions(
            "agent_456", 
            ["session_1", "session_2"], 
            ChannelType.CHAT
        )
        
        # Verify
        assert result["success"] is True
        assert result["merged_session_id"] == "session_1"
        assert result["target_channel"] == ChannelType.CHAT.value
        assert result["sessions_merged"] == 2
        assert result["active_entities"] == 2  # Both entities merged
        
        # Verify secondary session was ended
        router_service.session_service.end_session.assert_called_once_with("session_2", "agent_456")

    async def test_merge_sessions_insufficient_sessions(self, router_service):
        """Test merge sessions with insufficient sessions."""
        result = await router_service.merge_sessions(
            "agent_456", 
            ["session_1"], 
            ChannelType.CHAT
        )
        
        assert result["success"] is False
        assert "At least 2 sessions required" in result["error"]

    async def test_learn_channel_preference(self, router_service):
        """Test channel preference learning."""
        # Simulate multiple voice sessions
        for i in range(8):
            await router_service.learn_channel_preference("agent_456", ChannelType.VOICE, 120.0)
        
        # Simulate fewer chat sessions
        for i in range(2):
            await router_service.learn_channel_preference("agent_456", ChannelType.CHAT, 60.0)
        
        # Check learned preference
        assert router_service.channel_preferences["agent_456"] == ChannelPreference.VOICE_PREFERRED
        
        # Check stats
        stats = router_service.usage_stats["agent_456"]
        assert stats.voice_sessions == 8
        assert stats.chat_sessions == 2
        assert stats.voice_duration == 960.0
        assert stats.chat_duration == 120.0

    async def test_get_active_sessions(self, router_service):
        """Test getting active sessions for an agent."""
        # Add active sessions
        session1 = ActiveChannelSession(
            session_id="session_1",
            channel=ChannelType.VOICE,
            agent_id="agent_456"
        )
        session2 = ActiveChannelSession(
            session_id="session_2",
            channel=ChannelType.CHAT,
            agent_id="agent_456"
        )
        
        router_service.active_sessions["agent_456"] = [session1, session2]
        
        # Execute
        result = await router_service.get_active_sessions("agent_456")
        
        # Verify
        assert len(result) == 2
        assert result[0]["session_id"] == "session_1"
        assert result[0]["channel"] == ChannelType.VOICE.value
        assert result[1]["session_id"] == "session_2"
        assert result[1]["channel"] == ChannelType.CHAT.value
        assert "duration" in result[0]

    async def test_cleanup_expired_sessions(self, router_service):
        """Test cleanup of expired sessions."""
        # Create expired and active sessions
        expired_time = datetime.utcnow() - timedelta(hours=1)
        recent_time = datetime.utcnow() - timedelta(minutes=5)
        
        expired_session = ActiveChannelSession(
            session_id="expired_session",
            channel=ChannelType.VOICE,
            agent_id="agent_456"
        )
        expired_session.last_activity = expired_time
        
        active_session = ActiveChannelSession(
            session_id="active_session",
            channel=ChannelType.CHAT,
            agent_id="agent_456"
        )
        active_session.last_activity = recent_time
        
        router_service.active_sessions["agent_456"] = [expired_session, active_session]
        
        # Execute cleanup
        cleaned_count = await router_service.cleanup_expired_sessions()
        
        # Verify
        assert cleaned_count == 1
        assert len(router_service.active_sessions["agent_456"]) == 1
        assert router_service.active_sessions["agent_456"][0].session_id == "active_session"

    async def test_context_lock_creation(self, router_service):
        """Test context lock creation and reuse."""
        lock1 = router_service._get_context_lock("session_1")
        lock2 = router_service._get_context_lock("session_1")
        lock3 = router_service._get_context_lock("session_2")
        
        # Same session should get same lock
        assert lock1 is lock2
        
        # Different session should get different lock
        assert lock1 is not lock3

    async def test_capture_chat_context(self, router_service):
        """Test capturing chat context."""
        # Setup mock context
        mock_context = SessionContext(
            currentIntent="track_container",
            activeEntities=[
                EntityReference(type="container", id="EFLU1234567", confidence=0.95),
                EntityReference(type="bl", id="ABC1234567", confidence=0.90)
            ],
            lastResponse="Found your containers",
            pendingActions=["clarify_location", "provide_details"]
        )
        
        router_service.chat_continuity.hydrate_context.return_value = mock_context
        
        # Execute
        result = await router_service._capture_chat_context("session_123", "agent_456")
        
        # Verify
        assert result is not None
        assert result["current_intent"] == "track_container"
        assert len(result["recent_entities"]) == 2
        assert result["last_response"] == "Found your containers"
        assert len(result["pending_clarifications"]) == 2

    async def test_capture_chat_context_none(self, router_service):
        """Test capturing chat context when none exists."""
        router_service.chat_continuity.hydrate_context.return_value = None
        
        result = await router_service._capture_chat_context("session_123", "agent_456")
        
        assert result is None

    async def test_register_and_unregister_active_session(self, router_service):
        """Test registering and unregistering active sessions."""
        # Register session
        await router_service._register_active_session("session_123", "agent_456", ChannelType.VOICE)
        
        # Verify registration
        assert "agent_456" in router_service.active_sessions
        assert len(router_service.active_sessions["agent_456"]) == 1
        assert router_service.active_sessions["agent_456"][0].session_id == "session_123"
        
        # Register another session for same agent
        await router_service._register_active_session("session_456", "agent_456", ChannelType.CHAT)
        
        # Verify both sessions
        assert len(router_service.active_sessions["agent_456"]) == 2
        
        # Unregister one session
        await router_service._unregister_active_session("session_123", "agent_456")
        
        # Verify only one remains
        assert len(router_service.active_sessions["agent_456"]) == 1
        assert router_service.active_sessions["agent_456"][0].session_id == "session_456"
        
        # Unregister last session
        await router_service._unregister_active_session("session_456", "agent_456")
        
        # Verify agent removed from active sessions
        assert "agent_456" not in router_service.active_sessions

    async def test_setup_context_sync(self, router_service):
        """Test setting up context synchronization."""
        await router_service._setup_context_sync("primary_session", "secondary_session")
        
        # Verify sync queues were created
        assert "primary_session" in router_service.context_sync_queue
        assert "secondary_session" in router_service.context_sync_queue
        assert isinstance(router_service.context_sync_queue["primary_session"], list)
        assert isinstance(router_service.context_sync_queue["secondary_session"], list)

    async def test_sync_context_between_sessions(self, router_service):
        """Test synchronizing context between sessions."""
        # Setup sync queues
        await router_service._setup_context_sync("session_1", "session_2")
        
        # Sync context
        context_update = {"intent": "new_intent", "entities": ["entity1"]}
        await router_service._sync_context_between_sessions(
            "session_1", "session_2", context_update
        )
        
        # Verify sync queue
        sync_queue = router_service.context_sync_queue["session_2"]
        assert len(sync_queue) == 1
        assert sync_queue[0]["source"] == "session_1"
        assert sync_queue[0]["update"] == context_update
        assert "timestamp" in sync_queue[0]


class TestChannelUsageStats:
    """Test cases for ChannelUsageStats."""

    def test_default_initialization(self):
        """Test default initialization of usage stats."""
        stats = ChannelUsageStats()
        
        assert stats.voice_sessions == 0
        assert stats.chat_sessions == 0
        assert stats.voice_duration == 0.0
        assert stats.chat_duration == 0.0
        assert stats.voice_to_chat_switches == 0
        assert stats.chat_to_voice_switches == 0
        assert stats.last_used_channel is None
        assert isinstance(stats.last_activity, datetime)

    def test_custom_initialization(self):
        """Test custom initialization of usage stats."""
        last_activity = datetime.utcnow() - timedelta(hours=1)
        stats = ChannelUsageStats(
            voice_sessions=5,
            chat_sessions=3,
            voice_duration=300.0,
            chat_duration=180.0,
            last_used_channel=ChannelType.VOICE,
            last_activity=last_activity
        )
        
        assert stats.voice_sessions == 5
        assert stats.chat_sessions == 3
        assert stats.voice_duration == 300.0
        assert stats.chat_duration == 180.0
        assert stats.last_used_channel == ChannelType.VOICE
        assert stats.last_activity == last_activity


class TestActiveChannelSession:
    """Test cases for ActiveChannelSession."""

    def test_initialization(self):
        """Test ActiveChannelSession initialization."""
        session = ActiveChannelSession(
            session_id="test_session",
            channel=ChannelType.VOICE,
            agent_id="agent_123"
        )
        
        assert session.session_id == "test_session"
        assert session.channel == ChannelType.VOICE
        assert session.agent_id == "agent_123"
        assert isinstance(session.start_time, datetime)
        assert isinstance(session.last_activity, datetime)
        assert session.context_hash == ""

    def test_update_activity(self):
        """Test updating activity timestamp."""
        session = ActiveChannelSession(
            session_id="test_session",
            channel=ChannelType.VOICE,
            agent_id="agent_123"
        )
        
        original_time = session.last_activity
        
        # Wait a tiny bit to ensure time difference
        import time
        time.sleep(0.01)
        
        session.update_activity()
        
        assert session.last_activity > original_time


@pytest.mark.asyncio
class TestChannelRouterIntegration:
    """Integration tests for channel routing scenarios."""

    @pytest.fixture
    async def full_router_service(self):
        """Create a fully mocked router service for integration tests."""
        service = ChannelRouterService()
        
        # Create more realistic mocks
        service.session_service = AsyncMock()
        service.chat_continuity = AsyncMock()
        service.voice_continuity = AsyncMock()
        
        return await service.get_instance()

    async def test_complete_voice_to_chat_handoff(self, full_router_service):
        """Test complete handoff from voice to chat."""
        # Setup initial voice session
        voice_session = AgentSession(
            id="voice_session_123",
            agentId="agent_456",
            channel=ChannelType.VOICE,
            startTime=datetime.utcnow(),
            status=SessionStatus.ACTIVE,
            context=SessionContext(
                currentIntent="track_container",
                activeEntities=[EntityReference(type="container", id="EFLU1234567", confidence=0.95)],
                lastResponse="I found container EFLU1234567 in the yard",
                pendingActions=[]
            ),
            conversationHistory=[]
        )
        
        # Mock voice context
        voice_context = {
            "current_intent": "track_container",
            "recent_entities": [{"type": "container", "id": "EFLU1234567", "confidence": 0.95}],
            "conversation_turns": 2,
            "pending_clarifications": [],
            "context_variables": {}
        }
        
        # Setup mocks
        full_router_service.session_service.get_session.return_value = voice_session
        full_router_service.voice_continuity.get_session_context.return_value = voice_context
        full_router_service.chat_continuity.continue_from_voice.return_value = voice_session
        
        # Execute handoff
        result = await full_router_service.route_to_chat(
            "voice_session_123", 
            "agent_456", 
            preserve_voice_context=True
        )
        
        # Verify successful handoff
        assert result["success"] is True
        assert result["channel"] == ChannelType.CHAT.value
        assert result["context_preserved"] is True
        
        # Verify context was transferred
        full_router_service.chat_continuity.continue_from_voice.assert_called_once()
        call_args = full_router_service.chat_continuity.continue_from_voice.call_args
        assert call_args[0][0] == "voice_session_123"
        assert call_args[0][1] == "agent_456"
        assert call_args[0][2] == voice_context

    async def test_simultaneous_channels_with_context_sync(self, full_router_service):
        """Test simultaneous channels with context synchronization."""
        # Setup primary session
        primary_session = AgentSession(
            id="primary_session",
            agentId="agent_456",
            channel=ChannelType.CHAT,
            startTime=datetime.utcnow(),
            status=SessionStatus.ACTIVE,
            context=SessionContext(
                currentIntent="track_multiple_containers",
                activeEntities=[
                    EntityReference(type="container", id="EFLU1111111", confidence=0.95),
                    EntityReference(type="container", id="EFLU2222222", confidence=0.90)
                ],
                lastResponse="I found both containers",
                pendingActions=["provide_locations"]
            ),
            conversationHistory=[]
        )
        
        # Setup mocks
        full_router_service.session_service.get_session.return_value = primary_session
        full_router_service.route_to_voice = AsyncMock(return_value={"success": True})
        
        # Enable simultaneous channels
        result = await full_router_service.enable_simultaneous_channels(
            "agent_456",
            "primary_session",
            ChannelType.VOICE
        )
        
        # Verify success
        assert result["success"] is True
        assert result["context_synced"] is True
        assert "secondary_session_id" in result
        
        # Verify secondary session ID format
        secondary_id = result["secondary_session_id"]
        assert secondary_id.startswith("primary_session_")
        assert secondary_id.endswith("_voice")

    async def test_preference_learning_over_time(self, full_router_service):
        """Test that channel preferences are learned over time."""
        agent_id = "learning_agent_123"
        
        # Simulate user heavily preferring voice
        for i in range(10):
            await full_router_service.learn_channel_preference(
                agent_id, ChannelType.VOICE, 180.0  # 3 minutes average
            )
        
        # Simulate occasional chat usage
        for i in range(2):
            await full_router_service.learn_channel_preference(
                agent_id, ChannelType.CHAT, 60.0  # 1 minute average
            )
        
        # Check learned preference
        preference = full_router_service.channel_preferences.get(agent_id)
        assert preference == ChannelPreference.VOICE_PREFERRED
        
        # Test optimal channel selection
        optimal_channel = await full_router_service.get_optimal_channel(agent_id)
        assert optimal_channel == ChannelType.VOICE
        
        # Verify usage statistics
        stats = full_router_service.usage_stats[agent_id]
        assert stats.voice_sessions == 10
        assert stats.chat_sessions == 2
        assert stats.voice_duration == 1800.0  # 30 minutes total
        assert stats.chat_duration == 120.0    # 2 minutes total