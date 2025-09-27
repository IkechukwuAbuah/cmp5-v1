"""Unit tests for SessionService (T065)."""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock
from typing import List

from src.models.agent import (
    Agent,
    AgentSession,
    ChannelType,
    SessionContext,
    SessionStatus,
    Message,
    AgentType,
    ContactInfo,
    Permission,
    EntityReference
)
from src.services.session_service import SessionService


def _make_permission(resource: str) -> Permission:
    """Helper to build permission instances."""
    return Permission(resource=resource, actions=["read"], conditions=None)


def _make_agent(agent_id: str = "agent_123") -> Agent:
    """Create a sample agent for testing."""
    return Agent(
        id=agent_id,
        name="Test Agent",
        type=AgentType.CLEARING,
        contactInfo=ContactInfo(
            phone="+2347012345678",
            email="agent@example.com",
            companyName="Test Company"
        ),
        permissions=[_make_permission("container"), _make_permission("bl")],
    )


def _make_message(msg_id: str = "msg_1", msg_type: str = "user", content: str = "Hello") -> Message:
    """Create a sample message."""
    return Message(
        id=msg_id,
        type=msg_type,
        content=content,
        timestamp=datetime.utcnow()
    )


def _make_session_context() -> SessionContext:
    """Create a sample session context."""
    return SessionContext(
        currentIntent="track_container",
        activeEntities=[],
        lastResponse="",
        pendingActions=[]
    )


def _make_session(
    session_id: str = "sess_123",
    agent_id: str = "agent_123",
    channel: ChannelType = ChannelType.CHAT,
    status: SessionStatus = SessionStatus.ACTIVE
) -> AgentSession:
    """Create a sample session."""
    return AgentSession(
        id=session_id,
        agentId=agent_id,
        channel=channel,
        startTime=datetime.utcnow(),
        status=status,
        context=_make_session_context(),
        conversationHistory=[]
    )


@pytest.fixture
def session_service():
    """Create a SessionService instance for testing."""
    service = SessionService()
    # Mock dependencies to avoid initialization overhead
    service.degradation_service = AsyncMock()
    service.redis_session_store = AsyncMock()
    return service


@pytest.fixture
def mock_redis_store():
    """Create a mock Redis session store."""
    mock_store = AsyncMock()
    mock_store.save_session = AsyncMock(return_value=True)
    mock_store.load_session = AsyncMock(return_value=None)
    mock_store.delete_session = AsyncMock(return_value=True)
    return mock_store


class TestSessionServiceInitialization:
    """Test SessionService initialization and dependency management."""

    @pytest.mark.asyncio
    async def test_get_instance_initializes_dependencies(self):
        """Test that get_instance properly initializes dependencies."""
        service = SessionService()

        with patch('src.services.session_service.GracefulDegradationService.get_instance') as mock_degradation, \
             patch('src.services.session_service.get_redis_session_store') as mock_redis:

            mock_degradation.return_value = AsyncMock()
            mock_redis.return_value = AsyncMock()

            result = await service.get_instance()

            assert result is service
            assert service.degradation_service is not None
            assert service.redis_session_store is not None
            mock_degradation.assert_called_once()
            mock_redis.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_instance_reuses_existing_dependencies(self):
        """Test that get_instance doesn't reinitialize existing dependencies."""
        service = SessionService()
        service.degradation_service = AsyncMock()
        service.redis_session_store = AsyncMock()

        with patch('src.services.session_service.GracefulDegradationService.get_instance') as mock_degradation, \
             patch('src.services.session_service.get_redis_session_store') as mock_redis:

            result = await service.get_instance()

            assert result is service
            mock_degradation.assert_not_called()
            mock_redis.assert_not_called()


class TestSessionCRUDOperations:
    """Test core CRUD operations for sessions."""

    @pytest.mark.asyncio
    async def test_create_session_voice_channel(self, session_service):
        """Test creating a session for voice channel."""
        agent_id = "agent_123"
        channel = ChannelType.VOICE

        session = await session_service.create_session(agent_id, channel)

        assert session.agentId == agent_id
        assert session.channel == channel
        assert session.status == SessionStatus.ACTIVE
        assert session.id is not None
        assert session.startTime is not None
        assert session.endTime is None
        assert len(session.conversationHistory) == 0
        assert session.context.currentIntent is None
        assert len(session.context.activeEntities) == 0

        # Verify session is stored in memory
        assert session.id in session_service._sessions

    @pytest.mark.asyncio
    async def test_create_session_chat_channel(self, session_service):
        """Test creating a session for chat channel."""
        agent_id = "agent_456"
        channel = ChannelType.CHAT

        session = await session_service.create_session(agent_id, channel)

        assert session.agentId == agent_id
        assert session.channel == channel
        assert session.status == SessionStatus.ACTIVE
        assert session.id in session_service._sessions

    @pytest.mark.asyncio
    async def test_get_session_success(self, session_service):
        """Test retrieving an existing session."""
        # Create a session first
        session = await session_service.create_session("agent_123", ChannelType.CHAT)

        # Retrieve the session
        retrieved = await session_service.get_session(session.id, "agent_123")

        assert retrieved is not None
        assert retrieved.id == session.id
        assert retrieved.agentId == session.agentId

    @pytest.mark.asyncio
    async def test_get_session_different_agent_access_denied(self, session_service):
        """Test that agents cannot access other agents' sessions."""
        # Create a session for agent_123
        session = await session_service.create_session("agent_123", ChannelType.CHAT)

        # Try to access with different agent
        retrieved = await session_service.get_session(session.id, "agent_456")

        assert retrieved is None

    @pytest.mark.asyncio
    async def test_get_session_nonexistent(self, session_service):
        """Test retrieving a non-existent session."""
        session_service.redis_session_store.load_session = AsyncMock(return_value=None)

        retrieved = await session_service.get_session("nonexistent", "agent_123")

        assert retrieved is None

    @pytest.mark.asyncio
    async def test_get_session_expired(self, session_service, monkeypatch):
        """Test retrieving an expired session."""
        # Create a session
        session = await session_service.create_session("agent_123", ChannelType.CHAT)

        # Mock the expiration check to return True
        monkeypatch.setattr(session_service, '_is_session_expired', lambda s: True)

        retrieved = await session_service.get_session(session.id, "agent_123")

        assert retrieved is not None
        assert retrieved.status == SessionStatus.EXPIRED

    @pytest.mark.asyncio
    async def test_update_session_context_success(self, session_service):
        """Test updating session context."""
        # Create a session
        session = await session_service.create_session("agent_123", ChannelType.CHAT)

        # Create new context
        new_context = SessionContext(
            currentIntent="book_service",
            activeEntities=[EntityReference(type="container", id="EFLU1234567", confidence=0.95)],
            lastResponse="Container tracked successfully",
            pendingActions=["schedule_exam"]
        )

        # Update context
        result = await session_service.update_session_context(session.id, new_context)

        assert result is True
        assert session_service._sessions[session.id].context == new_context

    @pytest.mark.asyncio
    async def test_update_session_context_nonexistent(self, session_service):
        """Test updating context for non-existent session."""
        new_context = _make_session_context()

        result = await session_service.update_session_context("nonexistent", new_context)

        assert result is False

    @pytest.mark.asyncio
    async def test_end_session_success(self, session_service, mock_redis_store):
        """Test ending a session successfully."""
        session_service.redis_session_store = mock_redis_store

        # Create a session
        session = await session_service.create_session("agent_123", ChannelType.CHAT)

        # End the session
        result = await session_service.end_session(session.id, "agent_123")

        assert result is True
        assert session_service._sessions[session.id].status == SessionStatus.COMPLETED
        assert session_service._sessions[session.id].endTime is not None
        mock_redis_store.save_session.assert_called_once()

    @pytest.mark.asyncio
    async def test_end_session_nonexistent(self, session_service):
        """Test ending a non-existent session."""
        session_service.redis_session_store.load_session = AsyncMock(return_value=None)

        result = await session_service.end_session("nonexistent", "agent_123")

        assert result is False


class TestMessageManagement:
    """Test message handling in sessions."""

    @pytest.mark.asyncio
    async def test_add_message_success(self, session_service, monkeypatch):
        """Test adding a message to a session."""
        # Create a session
        session = await session_service.create_session("agent_123", ChannelType.CHAT)

        # Mock the context update method
        mock_update_context = AsyncMock()
        monkeypatch.setattr(session_service, '_update_context_from_message', mock_update_context)

        # Create a message
        message = _make_message("msg_1", "user", "Track container EFLU1234567")

        # Add message
        result = await session_service.add_message(session.id, message)

        assert result is True
        assert len(session_service._sessions[session.id].conversationHistory) == 1
        assert session_service._sessions[session.id].conversationHistory[0] == message
        mock_update_context.assert_called_once()

    @pytest.mark.asyncio
    async def test_add_message_enforces_max_limit(self, session_service, monkeypatch):
        """Test that messages are limited to MAX_SESSION_MESSAGES."""
        # Mock settings.MAX_SESSION_MESSAGES
        with patch('src.services.session_service.settings.MAX_SESSION_MESSAGES', 2):
            # Create a session
            session = await session_service.create_session("agent_123", ChannelType.CHAT)

            # Mock the context update method
            mock_update_context = AsyncMock()
            monkeypatch.setattr(session_service, '_update_context_from_message', mock_update_context)

            # Add 3 messages (exceeding limit of 2)
            for i in range(3):
                message = _make_message(f"msg_{i}", "user", f"Message {i}")
                await session_service.add_message(session.id, message)

            # Should only have the last 2 messages
            history = session_service._sessions[session.id].conversationHistory
            assert len(history) == 2
            assert history[0].content == "Message 1"
            assert history[1].content == "Message 2"

    @pytest.mark.asyncio
    async def test_add_message_nonexistent_session(self, session_service):
        """Test adding a message to non-existent session."""
        message = _make_message()

        result = await session_service.add_message("nonexistent", message)

        assert result is False

    @pytest.mark.asyncio
    async def test_get_session_messages_success(self, session_service):
        """Test retrieving messages from a session."""
        # Create a session
        session = await session_service.create_session("agent_123", ChannelType.CHAT)

        # Add some messages
        messages = [
            _make_message("msg_1", "user", "Hello"),
            _make_message("msg_2", "assistant", "Hi there!"),
            _make_message("msg_3", "user", "Track EFLU1234567")
        ]

        for msg in messages:
            session_service._sessions[session.id].conversationHistory.append(msg)

        # Get messages
        retrieved = await session_service.get_session_messages(session.id, "agent_123")

        assert len(retrieved) == 3
        assert retrieved == messages

    @pytest.mark.asyncio
    async def test_get_session_messages_with_limit(self, session_service):
        """Test retrieving messages with limit."""
        # Create a session
        session = await session_service.create_session("agent_123", ChannelType.CHAT)

        # Add 5 messages
        for i in range(5):
            message = _make_message(f"msg_{i}", "user", f"Message {i}")
            session_service._sessions[session.id].conversationHistory.append(message)

        # Get last 3 messages
        retrieved = await session_service.get_session_messages(session.id, "agent_123", limit=3)

        assert len(retrieved) == 3
        assert retrieved[0].content == "Message 2"
        assert retrieved[1].content == "Message 3"
        assert retrieved[2].content == "Message 4"

    @pytest.mark.asyncio
    async def test_get_session_messages_nonexistent_session(self, session_service):
        """Test retrieving messages from non-existent session."""
        session_service.redis_session_store.load_session = AsyncMock(return_value=None)

        retrieved = await session_service.get_session_messages("nonexistent", "agent_123")

        assert retrieved == []


class TestMultiChannelSupport:
    """Test multi-channel session continuity."""

    @pytest.mark.asyncio
    async def test_switch_channel_voice_to_chat(self, session_service):
        """Test switching from voice to chat channel."""
        # Create a voice session
        session = await session_service.create_session("agent_123", ChannelType.VOICE)

        # Add some conversation history
        message = _make_message("msg_1", "user", "Track container EFLU1234567")
        await session_service.add_message(session.id, message)

        # Switch to chat
        switched = await session_service.switch_channel(session.id, "agent_123", ChannelType.CHAT)

        assert switched is not None
        assert switched.channel == ChannelType.CHAT
        assert len(switched.conversationHistory) == 1  # History preserved
        assert switched.context.currentIntent is not None  # Context preserved

    @pytest.mark.asyncio
    async def test_switch_channel_chat_to_voice(self, session_service):
        """Test switching from chat to voice channel."""
        # Create a chat session
        session = await session_service.create_session("agent_123", ChannelType.CHAT)

        # Add context
        context = SessionContext(
            currentIntent="track_container",
            activeEntities=[EntityReference(type="container", id="EFLU1234567", confidence=0.95)],
            lastResponse="Container found",
            pendingActions=[]
        )
        await session_service.update_session_context(session.id, context)

        # Switch to voice
        switched = await session_service.switch_channel(session.id, "agent_123", ChannelType.VOICE)

        assert switched is not None
        assert switched.channel == ChannelType.VOICE
        assert switched.context.currentIntent == "track_container"
        assert len(switched.context.activeEntities) == 1

    @pytest.mark.asyncio
    async def test_switch_channel_nonexistent_session(self, session_service):
        """Test switching channel for non-existent session."""
        session_service.redis_session_store.load_session = AsyncMock(return_value=None)

        result = await session_service.switch_channel("nonexistent", "agent_123", ChannelType.VOICE)

        assert result is None

    @pytest.mark.asyncio
    async def test_switch_channel_different_agent(self, session_service):
        """Test that channel switching respects agent ownership."""
        # Create a session for agent_123
        session = await session_service.create_session("agent_123", ChannelType.CHAT)

        # Try to switch channel with different agent
        session_service.redis_session_store.load_session = AsyncMock(return_value=None)
        result = await session_service.switch_channel(session.id, "agent_456", ChannelType.VOICE)

        assert result is None


class TestSessionTimeout:
    """Test session timeout and expiration logic."""

    def test_is_session_expired_active_within_timeout(self, session_service):
        """Test that active sessions within timeout are not expired."""
        session = _make_session()
        session.startTime = datetime.utcnow() - timedelta(minutes=10)  # 10 minutes ago

        with patch('src.services.session_service.settings.SESSION_TIMEOUT_MINUTES', 30):
            result = session_service._is_session_expired(session)

        assert result is False

    def test_is_session_expired_active_beyond_timeout(self, session_service):
        """Test that active sessions beyond timeout are expired."""
        session = _make_session()
        session.startTime = datetime.utcnow() - timedelta(minutes=60)  # 1 hour ago

        with patch('src.services.session_service.settings.SESSION_TIMEOUT_MINUTES', 30):
            result = session_service._is_session_expired(session)

        assert result is True

    def test_is_session_expired_with_recent_message(self, session_service):
        """Test that sessions with recent messages are not expired."""
        session = _make_session()
        session.startTime = datetime.utcnow() - timedelta(minutes=60)  # 1 hour ago

        # Add a recent message
        recent_message = _make_message()
        recent_message.timestamp = datetime.utcnow() - timedelta(minutes=10)
        session.conversationHistory = [recent_message]

        with patch('src.services.session_service.settings.SESSION_TIMEOUT_MINUTES', 30):
            result = session_service._is_session_expired(session)

        assert result is False

    def test_is_session_expired_non_active_status(self, session_service):
        """Test that non-active sessions are not checked for expiration."""
        session = _make_session(status=SessionStatus.COMPLETED)
        session.startTime = datetime.utcnow() - timedelta(minutes=60)

        with patch('src.services.session_service.settings.SESSION_TIMEOUT_MINUTES', 30):
            result = session_service._is_session_expired(session)

        assert result is False

    def test_get_session_last_activity_with_messages(self, session_service):
        """Test getting last activity when session has messages."""
        session = _make_session()

        message1 = _make_message("msg_1")
        message1.timestamp = datetime.utcnow() - timedelta(minutes=30)

        message2 = _make_message("msg_2")
        message2.timestamp = datetime.utcnow() - timedelta(minutes=10)

        session.conversationHistory = [message1, message2]

        last_activity = session_service._get_session_last_activity(session)

        assert last_activity == message2.timestamp

    def test_get_session_last_activity_no_messages(self, session_service):
        """Test getting last activity when session has no messages."""
        session = _make_session()
        session.conversationHistory = []

        last_activity = session_service._get_session_last_activity(session)

        assert last_activity == session.startTime

    @pytest.mark.asyncio
    async def test_cleanup_expired_sessions(self, session_service, monkeypatch):
        """Test cleanup of expired sessions."""
        # Create multiple sessions
        active_session = await session_service.create_session("agent_123", ChannelType.CHAT)
        expired_session1 = await session_service.create_session("agent_456", ChannelType.VOICE)
        expired_session2 = await session_service.create_session("agent_789", ChannelType.CHAT)

        # Mock expiration check to mark some as expired
        def mock_is_expired(session):
            return session.id in [expired_session1.id, expired_session2.id]

        monkeypatch.setattr(session_service, '_is_session_expired', mock_is_expired)

        # Run cleanup
        await session_service.cleanup_expired_sessions()

        # Check results
        assert active_session.id in session_service._sessions
        assert expired_session1.id not in session_service._sessions
        assert expired_session2.id not in session_service._sessions

        # Check that expired sessions have status updated
        assert session_service._sessions[active_session.id].status == SessionStatus.ACTIVE


class TestSessionStats:
    """Test session statistics functionality."""

    @pytest.mark.asyncio
    async def test_get_session_stats(self, session_service):
        """Test getting session statistics."""
        # Create sessions with different statuses
        active1 = await session_service.create_session("agent_123", ChannelType.CHAT)
        active2 = await session_service.create_session("agent_456", ChannelType.VOICE)

        completed = await session_service.create_session("agent_789", ChannelType.CHAT)
        session_service._sessions[completed.id].status = SessionStatus.COMPLETED

        expired = await session_service.create_session("agent_101", ChannelType.VOICE)
        session_service._sessions[expired.id].status = SessionStatus.EXPIRED

        # Get stats
        stats = session_service.get_session_stats()

        assert stats["total_sessions"] == 4
        assert stats["active_sessions"] == 2
        assert stats["expired_sessions"] == 1

    def test_get_session_stats_empty(self, session_service):
        """Test getting stats when no sessions exist."""
        stats = session_service.get_session_stats()

        assert stats["total_sessions"] == 0
        assert stats["active_sessions"] == 0
        assert stats["expired_sessions"] == 0


class TestContextPreservation:
    """Test session context preservation and updates."""

    @pytest.mark.asyncio
    async def test_update_context_from_user_message(self, session_service):
        """Test context update when processing user messages."""
        session = _make_session()
        session_service._sessions[session.id] = session

        # User message with tracking intent
        message = _make_message("msg_1", "user", "Track container EFLU1234567")

        await session_service._update_context_from_message(session, message)

        # Check intent inference
        assert session.context.currentIntent == "track_container"
        assert session.context.lastResponse == ""

        # Check entity extraction
        assert len(session.context.activeEntities) == 1
        assert session.context.activeEntities[0]["type"] == "container"
        assert session.context.activeEntities[0]["id"] == "EFLU1234567"

    @pytest.mark.asyncio
    async def test_update_context_from_assistant_message(self, session_service):
        """Test context update when processing assistant messages."""
        session = _make_session()
        session.context.currentIntent = "track_container"
        session_service._sessions[session.id] = session

        # Assistant response
        message = _make_message("msg_2", "assistant", "Container EFLU1234567 is at terminal")

        await session_service._update_context_from_message(session, message)

        # Intent should remain, last response updated
        assert session.context.currentIntent == "track_container"
        assert session.context.lastResponse == "Container EFLU1234567 is at terminal"

    @pytest.mark.asyncio
    async def test_context_preserved_across_channel_switch(self, session_service, monkeypatch):
        """Test that context is fully preserved when switching channels."""
        # Mock the context update method
        mock_update_context = AsyncMock()
        monkeypatch.setattr(session_service, '_update_context_from_message', mock_update_context)

        # Create and populate session
        session = await session_service.create_session("agent_123", ChannelType.CHAT)

        # Set rich context
        context = SessionContext(
            currentIntent="book_service",
            activeEntities=[
                {"type": "container", "id": "EFLU1234567", "confidence": 0.95},
                {"type": "bl", "id": "ABC7654321", "confidence": 0.90}
            ],
            lastResponse="Booking confirmed",
            pendingActions=["confirm_payment", "schedule_pickup"]
        )
        await session_service.update_session_context(session.id, context)

        # Add conversation history
        messages = [
            _make_message("msg_1", "user", "Book service for EFLU1234567"),
            _make_message("msg_2", "assistant", "Booking confirmed")
        ]
        for msg in messages:
            await session_service.add_message(session.id, msg)

        # Switch channel
        switched = await session_service.switch_channel(session.id, "agent_123", ChannelType.VOICE)

        # Verify everything is preserved
        assert switched.context.currentIntent == "book_service"
        assert len(switched.context.activeEntities) == 2
        assert switched.context.lastResponse == "Booking confirmed"
        assert len(switched.context.pendingActions) == 2
        assert len(switched.conversationHistory) == 2

    def test_infer_intent_tracking(self, session_service):
        """Test intent inference for tracking requests."""
        tracking_messages = [
            "Track container EFLU1234567",
            "Where is my container?",
            "What's the status of my shipment?"
        ]

        for msg in tracking_messages:
            intent = session_service._infer_intent(msg)
            assert intent == "track_container"

    def test_infer_intent_help(self, session_service):
        """Test intent inference for help requests."""
        help_messages = [
            "I need help",
            "What can you do?",
            "How does this work?"
        ]

        for msg in help_messages:
            intent = session_service._infer_intent(msg)
            assert intent == "get_help"

    def test_infer_intent_booking(self, session_service):
        """Test intent inference for booking requests."""
        booking_messages = [
            "Book a customs examination",
            "Schedule a pickup",
            "Arrange delivery"
        ]

        for msg in booking_messages:
            intent = session_service._infer_intent(msg)
            assert intent == "book_service"

    def test_infer_intent_general(self, session_service):
        """Test intent inference for general inquiries."""
        general_messages = [
            "Hello",
            "Thank you",
            "Good morning"
        ]

        for msg in general_messages:
            intent = session_service._infer_intent(msg)
            assert intent == "general_inquiry"

    def test_extract_entities_containers(self, session_service):
        """Test extracting container IDs from messages."""
        message = "Track containers EFLU1234567 and EFLU7654321"

        entities = session_service._extract_entities_from_message(message)

        assert len(entities) == 2
        assert entities[0]["type"] == "container"
        assert entities[0]["id"] == "EFLU1234567"
        assert entities[0]["confidence"] == 0.95
        assert entities[1]["type"] == "container"
        assert entities[1]["id"] == "EFLU7654321"

    def test_extract_entities_bl_numbers(self, session_service):
        """Test extracting BL numbers from messages."""
        message = "Check BL ABC1234567 and ABC7654321"

        entities = session_service._extract_entities_from_message(message)

        assert len(entities) == 2
        assert entities[0]["type"] == "bl"
        assert entities[0]["id"] == "ABC1234567"
        assert entities[1]["type"] == "bl"
        assert entities[1]["id"] == "ABC7654321"

    def test_extract_entities_mixed(self, session_service):
        """Test extracting mixed entity types."""
        message = "Track container EFLU1234567 and BL ABC7654321"

        entities = session_service._extract_entities_from_message(message)

        assert len(entities) == 2
        assert entities[0]["type"] == "container"
        assert entities[0]["id"] == "EFLU1234567"
        assert entities[1]["type"] == "bl"
        assert entities[1]["id"] == "ABC7654321"

    def test_extract_entities_case_insensitive(self, session_service):
        """Test entity extraction is case-insensitive."""
        message = "track container eflu1234567 and bl abc7654321"

        entities = session_service._extract_entities_from_message(message)

        assert len(entities) == 2
        assert entities[0]["id"] == "EFLU1234567"  # Normalized to uppercase
        assert entities[1]["id"] == "ABC7654321"

    @pytest.mark.asyncio
    async def test_active_entities_limited(self, session_service):
        """Test that active entities list is limited to prevent memory issues."""
        session = _make_session()
        session_service._sessions[session.id] = session

        # Add many entities to exceed limit
        for i in range(15):
            message = _make_message(f"msg_{i}", "user", f"Track EFLU{i:07d}")
            await session_service._update_context_from_message(session, message)

        # Should only keep last 10 entities
        assert len(session.context.activeEntities) == 10
        # Verify we have the most recent ones
        assert session.context.activeEntities[-1]["id"] == "EFLU0000014"


class TestErrorHandling:
    """Test error handling and edge cases."""

    @pytest.mark.asyncio
    async def test_load_session_from_storage_redis_error(self, session_service):
        """Test handling Redis errors when loading sessions."""
        session_service.redis_session_store.load_session = AsyncMock(side_effect=Exception("Redis connection failed"))

        result = await session_service._load_session_from_storage("sess_123", "agent_123")

        assert result is None

    @pytest.mark.asyncio
    async def test_load_session_from_storage_no_redis(self, session_service):
        """Test loading session when Redis store is not initialized."""
        session_service.redis_session_store = None

        result = await session_service._load_session_from_storage("sess_123", "agent_123")

        assert result is None

    @pytest.mark.asyncio
    async def test_persist_session_redis_error(self, session_service):
        """Test handling Redis errors when persisting sessions."""
        session = _make_session()
        session_service.redis_session_store.save_session = AsyncMock(side_effect=Exception("Redis write failed"))

        # Should not raise exception
        await session_service._persist_session(session)

        session_service.redis_session_store.save_session.assert_called_once()

    @pytest.mark.asyncio
    async def test_persist_session_no_redis(self, session_service):
        """Test persisting session when Redis store is not initialized."""
        session_service.redis_session_store = None
        session = _make_session()

        # Should handle gracefully without error
        await session_service._persist_session(session)

    @pytest.mark.asyncio
    async def test_get_session_from_storage_agent_mismatch(self, session_service):
        """Test that sessions loaded from storage validate agent ownership."""
        # Create session for different agent
        stored_session = _make_session(agent_id="agent_456")
        session_service.redis_session_store.load_session = AsyncMock(return_value=stored_session)

        result = await session_service._load_session_from_storage("sess_123", "agent_123")

        assert result is None  # Should reject due to agent mismatch

    @pytest.mark.asyncio
    async def test_concurrent_session_operations(self, session_service):
        """Test thread-safe concurrent session operations."""
        import asyncio

        async def create_and_update(agent_id):
            session = await session_service.create_session(agent_id, ChannelType.CHAT)
            for i in range(5):
                message = _make_message(f"msg_{i}", "user", f"Message {i}")
                await session_service.add_message(session.id, message)
            return session.id

        # Run multiple concurrent operations
        tasks = [create_and_update(f"agent_{i}") for i in range(10)]
        session_ids = await asyncio.gather(*tasks)

        # Verify all sessions created successfully
        assert len(session_ids) == 10
        assert len(set(session_ids)) == 10  # All unique

        # Verify each session has its messages
        for i, session_id in enumerate(session_ids):
            session = await session_service.get_session(session_id, f"agent_{i}")
            assert session is not None
            assert len(session.conversationHistory) == 5

    @pytest.mark.asyncio
    async def test_session_operations_with_invalid_data(self, session_service, monkeypatch):
        """Test handling of invalid data in session operations."""
        # Mock the context update method
        mock_update_context = AsyncMock()
        monkeypatch.setattr(session_service, '_update_context_from_message', mock_update_context)

        # Test with empty agent ID
        session = await session_service.create_session("", ChannelType.CHAT)
        assert session.agentId == ""

        # Test with invalid message type
        invalid_message = _make_message()
        invalid_message.type = "invalid_type"
        result = await session_service.add_message(session.id, invalid_message)
        assert result is True  # Should accept but handle appropriately

    @pytest.mark.asyncio
    async def test_cleanup_with_concurrent_access(self, session_service):
        """Test cleanup doesn't interfere with active session access."""
        import asyncio

        # Create sessions
        active_session = await session_service.create_session("agent_123", ChannelType.CHAT)
        expired_session = await session_service.create_session("agent_456", ChannelType.VOICE)

        # Mark one as expired
        expired_session.startTime = datetime.utcnow() - timedelta(hours=2)

        async def access_session():
            # Try to access session during cleanup
            for _ in range(10):
                await session_service.get_session(active_session.id, "agent_123")
                await asyncio.sleep(0.001)

        async def run_cleanup():
            await asyncio.sleep(0.005)  # Small delay
            with patch('src.services.session_service.settings.SESSION_TIMEOUT_MINUTES', 30):
                await session_service.cleanup_expired_sessions()

        # Run concurrently
        await asyncio.gather(access_session(), run_cleanup())

        # Active session should still be accessible
        session = await session_service.get_session(active_session.id, "agent_123")
        assert session is not None


class TestPersistenceIntegration:
    """Test integration with Redis persistence layer."""

    @pytest.mark.asyncio
    async def test_session_loaded_from_storage_on_miss(self, session_service, mock_redis_store):
        """Test that sessions are loaded from storage when not in memory."""
        stored_session = _make_session("stored_123", "agent_123")
        mock_redis_store.load_session = AsyncMock(return_value=stored_session)
        session_service.redis_session_store = mock_redis_store

        # Session not in memory
        assert "stored_123" not in session_service._sessions

        # Get session should load from storage
        result = await session_service.get_session("stored_123", "agent_123")

        assert result is not None
        assert result.id == "stored_123"
        mock_redis_store.load_session.assert_called_once_with("stored_123")

    @pytest.mark.asyncio
    async def test_session_persisted_on_end(self, session_service, mock_redis_store):
        """Test that sessions are persisted when ended."""
        session_service.redis_session_store = mock_redis_store

        # Create and end session
        session = await session_service.create_session("agent_123", ChannelType.CHAT)
        await session_service.end_session(session.id, "agent_123")

        # Verify persistence
        mock_redis_store.save_session.assert_called_once()
        saved_session = mock_redis_store.save_session.call_args[0][0]
        assert saved_session.id == session.id
        assert saved_session.status == SessionStatus.COMPLETED
        assert saved_session.endTime is not None

    @pytest.mark.asyncio
    async def test_graceful_degradation_without_redis(self, session_service):
        """Test that system works without Redis (in-memory only)."""
        session_service.redis_session_store = None

        # Should still work with in-memory storage
        session = await session_service.create_session("agent_123", ChannelType.CHAT)
        assert session is not None

        # Operations should succeed
        message = _make_message()
        result = await session_service.add_message(session.id, message)
        assert result is True

        retrieved = await session_service.get_session(session.id, "agent_123")
        assert retrieved is not None

        # End session should work without persistence
        result = await session_service.end_session(session.id, "agent_123")
        assert result is True