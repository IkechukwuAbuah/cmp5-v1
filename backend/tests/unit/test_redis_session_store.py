"""Unit tests for Redis session store."""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock

from src.models.agent import AgentSession, SessionStatus, ChannelType, SessionContext, Message
from src.storage.redis_session_store import RedisSessionStore


@pytest.fixture
def redis_session_store():
    """Create a Redis session store instance for testing."""
    store = RedisSessionStore()
    # Mock the Redis client to avoid actual Redis connections during testing
    store.redis_client = AsyncMock()
    store._initialized = True
    return store


@pytest.fixture
def sample_session():
    """Create a sample session for testing."""
    return AgentSession(
        id="test_session_123",
        agentId="test_agent_456",
        channel=ChannelType.CHAT,
        startTime=datetime.utcnow(),
        status=SessionStatus.ACTIVE,
        context=SessionContext(
            currentIntent="track_container",
            activeEntities=[],
            lastResponse="",
            pendingActions=[]
        ),
        conversationHistory=[
            Message(
                id="msg_1",
                type="user",
                content="Track container EFLU7896543",
                timestamp=datetime.utcnow()
            )
        ]
    )


class TestRedisSessionStore:
    """Test cases for Redis session store functionality."""

    @pytest.mark.asyncio
    async def test_save_session_success(self, redis_session_store, sample_session):
        """Test successful session saving."""
        # Arrange
        redis_session_store.redis_client.setex = AsyncMock(return_value=True)

        # Act
        result = await redis_session_store.save_session(sample_session)

        # Assert
        assert result is True
        redis_session_store.redis_client.setex.assert_called_once()
        # Verify the key format
        call_args = redis_session_store.redis_client.setex.call_args
        assert call_args[0][0] == "session:test_session_123"

    @pytest.mark.asyncio
    async def test_save_session_failure(self, redis_session_store, sample_session):
        """Test session saving failure."""
        # Arrange
        redis_session_store.redis_client.setex = AsyncMock(side_effect=Exception("Redis error"))

        # Act
        result = await redis_session_store.save_session(sample_session)

        # Assert
        assert result is False

    @pytest.mark.asyncio
    async def test_load_session_success(self, redis_session_store, sample_session):
        """Test successful session loading."""
        # Arrange
        serialized_session = '{"id": "test_session_123", "agentId": "test_agent_456", "channel": "chat", "status": "active", "startTime": "2025-01-15T10:00:00", "context": {"currentIntent": null, "activeEntities": [], "lastResponse": "", "pendingActions": []}, "conversationHistory": [], "endTime": null}'
        redis_session_store.redis_client.get = AsyncMock(return_value=serialized_session)

        # Act
        result = await redis_session_store.load_session("test_session_123")

        # Assert
        assert result is not None
        assert result.id == "test_session_123"
        assert result.agentId == "test_agent_456"
        assert result.channel == ChannelType.CHAT
        assert result.status == SessionStatus.ACTIVE

    @pytest.mark.asyncio
    async def test_load_session_not_found(self, redis_session_store):
        """Test loading non-existent session."""
        # Arrange
        redis_session_store.redis_client.get = AsyncMock(return_value=None)

        # Act
        result = await redis_session_store.load_session("non_existent_session")

        # Assert
        assert result is None

    @pytest.mark.asyncio
    async def test_load_session_failure(self, redis_session_store):
        """Test session loading failure."""
        # Arrange
        redis_session_store.redis_client.get = AsyncMock(side_effect=Exception("Redis error"))

        # Act
        result = await redis_session_store.load_session("test_session_123")

        # Assert
        assert result is None

    @pytest.mark.asyncio
    async def test_delete_session_success(self, redis_session_store):
        """Test successful session deletion."""
        # Arrange
        redis_session_store.redis_client.delete = AsyncMock(return_value=1)

        # Act
        result = await redis_session_store.delete_session("test_session_123")

        # Assert
        assert result is True
        redis_session_store.redis_client.delete.assert_called_once_with("session:test_session_123")

    @pytest.mark.asyncio
    async def test_delete_session_not_found(self, redis_session_store):
        """Test deleting non-existent session."""
        # Arrange
        redis_session_store.redis_client.delete = AsyncMock(return_value=0)

        # Act
        result = await redis_session_store.delete_session("non_existent_session")

        # Assert
        assert result is False

    @pytest.mark.asyncio
    async def test_session_exists_true(self, redis_session_store):
        """Test session existence check when session exists."""
        # Arrange
        redis_session_store.redis_client.exists = AsyncMock(return_value=1)

        # Act
        result = await redis_session_store.session_exists("test_session_123")

        # Assert
        assert result is True
        redis_session_store.redis_client.exists.assert_called_once_with("session:test_session_123")

    @pytest.mark.asyncio
    async def test_session_exists_false(self, redis_session_store):
        """Test session existence check when session doesn't exist."""
        # Arrange
        redis_session_store.redis_client.exists = AsyncMock(return_value=0)

        # Act
        result = await redis_session_store.session_exists("non_existent_session")

        # Assert
        assert result is False

    @pytest.mark.asyncio
    async def test_get_session_ttl(self, redis_session_store):
        """Test getting session TTL."""
        # Arrange
        redis_session_store.redis_client.ttl = AsyncMock(return_value=3600)

        # Act
        result = await redis_session_store.get_session_ttl("test_session_123")

        # Assert
        assert result == 3600
        redis_session_store.redis_client.ttl.assert_called_once_with("session:test_session_123")

    @pytest.mark.asyncio
    async def test_extend_session_ttl_success(self, redis_session_store):
        """Test successful TTL extension."""
        # Arrange
        redis_session_store.redis_client.expire = AsyncMock(return_value=True)

        # Act
        result = await redis_session_store.extend_session_ttl("test_session_123")

        # Assert
        assert result is True
        redis_session_store.redis_client.expire.assert_called_once()

    @pytest.mark.asyncio
    async def test_cleanup_expired_sessions(self, redis_session_store):
        """Test cleanup of expired sessions."""
        # Arrange
        redis_session_store.redis_client.keys = AsyncMock(return_value=["session:expired_1", "session:expired_2"])
        redis_session_store.redis_client.ttl = AsyncMock(side_effect=[0, -1])  # Both expired
        redis_session_store.redis_client.delete = AsyncMock(return_value=2)

        # Act
        result = await redis_session_store.cleanup_expired_sessions()

        # Assert
        assert result == 2
        redis_session_store.redis_client.delete.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_session_count(self, redis_session_store):
        """Test getting session count."""
        # Arrange
        redis_session_store.redis_client.keys = AsyncMock(return_value=["session:1", "session:2", "session:3"])

        # Act
        result = await redis_session_store.get_session_count()

        # Assert
        assert result == 3
        redis_session_store.redis_client.keys.assert_called_once_with("session:*")

    def test_serialize_session(self, redis_session_store, sample_session):
        """Test session serialization."""
        # Act
        result = redis_session_store._serialize_session(sample_session)

        # Assert
        assert isinstance(result, str)
        # Verify it contains expected data
        assert "test_session_123" in result
        assert "test_agent_456" in result
        assert "chat" in result  # enum value
        assert "active" in result  # enum value

    def test_deserialize_session(self, redis_session_store, sample_session):
        """Test session deserialization."""
        # Arrange
        serialized = redis_session_store._serialize_session(sample_session)

        # Act
        result = redis_session_store._deserialize_session(serialized, "test_session_123")

        # Assert
        assert result is not None
        assert result.id == sample_session.id
        assert result.agentId == sample_session.agentId
        assert result.channel == sample_session.channel
        assert result.status == sample_session.status

    def test_deserialize_session_invalid_data(self, redis_session_store):
        """Test deserialization with invalid data."""
        # Act
        result = redis_session_store._deserialize_session("invalid json", "test_session")

        # Assert
        assert result is None

    @pytest.mark.asyncio
    async def test_close_redis_connection(self, redis_session_store):
        """Test closing Redis connections."""
        # Arrange
        redis_session_store.redis_client = AsyncMock()
        redis_session_store.connection_pool = AsyncMock()

        # Act
        await redis_session_store.close()

        # Assert
        redis_session_store.redis_client.close.assert_called_once()
        redis_session_store.connection_pool.disconnect.assert_called_once()
        assert redis_session_store._initialized is False
