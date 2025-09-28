"""Redis session store implementation for persistent session management."""

import json
import asyncio
from datetime import datetime
from typing import Optional, Dict, Any
import redis.asyncio as redis
from redis.asyncio.connection import ConnectionPool

from src.core.config import settings
from src.models.agent import ChannelType
from src.models.agent_session import AgentSession, SessionStatus

import logging
logger = logging.getLogger(__name__)


class RedisSessionStore:
    """Redis-based session store for persistent session management."""

    def __init__(self):
        self.redis_client: Optional[redis.Redis] = None
        self.connection_pool: Optional[ConnectionPool] = None
        self._initialized = False

    async def initialize(self) -> None:
        """Initialize Redis connection pool and client."""
        if self._initialized:
            return

        try:
            # Create connection pool with configuration
            self.connection_pool = ConnectionPool.from_url(
                settings.REDIS_URL,
                max_connections=settings.REDIS_MAX_CONNECTIONS,
                retry_on_timeout=True,
                socket_connect_timeout=5,
                socket_keepalive=True,
                socket_keepalive_options={},
                health_check_interval=30
            )

            # Create Redis client
            self.redis_client = redis.Redis(
                connection_pool=self.connection_pool,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_keepalive=True,
                socket_keepalive_options={},
                health_check_interval=30
            )

            # Test connection
            await self.redis_client.ping()
            self._initialized = True
            logger.info("Redis session store initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize Redis session store: {str(e)}")
            raise

    async def get_instance(self) -> "RedisSessionStore":
        """Get singleton instance with lazy initialization."""
        if not self._initialized:
            await self.initialize()
        return self

    def _serialize_session(self, session: AgentSession) -> str:
        """Serialize AgentSession to JSON string."""
        try:
            # Convert session to dictionary
            session_dict = session.dict()

            # Handle datetime serialization
            if session.startTime:
                session_dict['startTime'] = session.startTime.isoformat()
            if session.endTime:
                session_dict['endTime'] = session.endTime.isoformat()

            # Handle enum serialization
            session_dict['channel'] = session.channel.value
            session_dict['status'] = session.status.value

            # Handle conversation history
            for i, message in enumerate(session.conversationHistory):
                if message.timestamp:
                    session_dict['conversationHistory'][i]['timestamp'] = message.timestamp.isoformat()

            return json.dumps(session_dict, ensure_ascii=False)

        except Exception as e:
            logger.error(f"Failed to serialize session {session.id}: {str(e)}")
            raise

    def _deserialize_session(self, session_data: str, session_id: str) -> Optional[AgentSession]:
        """Deserialize JSON string to AgentSession object."""
        try:
            session_dict = json.loads(session_data)

            # Handle datetime deserialization
            if session_dict.get('startTime'):
                session_dict['startTime'] = datetime.fromisoformat(session_dict['startTime'])
            if session_dict.get('endTime'):
                session_dict['endTime'] = datetime.fromisoformat(session_dict['endTime'])

            # Handle enum deserialization
            session_dict['channel'] = ChannelType(session_dict['channel'])
            session_dict['status'] = SessionStatus(session_dict['status'])

            # Handle conversation history
            if 'conversationHistory' in session_dict:
                for i, message in enumerate(session_dict['conversationHistory']):
                    if message.get('timestamp'):
                        session_dict['conversationHistory'][i]['timestamp'] = datetime.fromisoformat(message['timestamp'])

            return AgentSession(**session_dict)

        except Exception as e:
            logger.error(f"Failed to deserialize session {session_id}: {str(e)}")
            return None

    async def save_session(self, session: AgentSession) -> bool:
        """Save session to Redis with TTL."""
        if not self._initialized or not self.redis_client:
            logger.error("Redis session store not initialized")
            return False

        try:
            # Serialize session
            serialized_session = self._serialize_session(session)

            # Save to Redis with TTL
            key = f"session:{session.id}"
            await self.redis_client.setex(
                key,
                settings.REDIS_SESSION_TTL,
                serialized_session
            )

            logger.debug(f"Session {session.id} saved to Redis")
            return True

        except Exception as e:
            logger.error(f"Failed to save session {session.id}: {str(e)}")
            return False

    async def load_session(self, session_id: str) -> Optional[AgentSession]:
        """Load session from Redis."""
        if not self._initialized or not self.redis_client:
            logger.error("Redis session store not initialized")
            return None

        try:
            key = f"session:{session_id}"
            session_data = await self.redis_client.get(key)

            if not session_data:
                logger.debug(f"Session {session_id} not found in Redis")
                return None

            # Deserialize session
            session = self._deserialize_session(session_data, session_id)
            if session:
                logger.debug(f"Session {session_id} loaded from Redis")

            return session

        except Exception as e:
            logger.error(f"Failed to load session {session_id}: {str(e)}")
            return None

    async def delete_session(self, session_id: str) -> bool:
        """Delete session from Redis."""
        if not self._initialized or not self.redis_client:
            logger.error("Redis session store not initialized")
            return False

        try:
            key = f"session:{session_id}"
            deleted = await self.redis_client.delete(key)

            if deleted:
                logger.debug(f"Session {session_id} deleted from Redis")
            else:
                logger.debug(f"Session {session_id} not found for deletion")

            return deleted > 0

        except Exception as e:
            logger.error(f"Failed to delete session {session_id}: {str(e)}")
            return False

    async def session_exists(self, session_id: str) -> bool:
        """Check if session exists in Redis."""
        if not self._initialized or not self.redis_client:
            return False

        try:
            key = f"session:{session_id}"
            exists = await self.redis_client.exists(key)
            return exists > 0

        except Exception as e:
            logger.error(f"Failed to check session existence {session_id}: {str(e)}")
            return False

    async def get_session_ttl(self, session_id: str) -> Optional[int]:
        """Get remaining TTL for session in seconds."""
        if not self._initialized or not self.redis_client:
            return None

        try:
            key = f"session:{session_id}"
            ttl = await self.redis_client.ttl(key)
            return ttl if ttl > 0 else None

        except Exception as e:
            logger.error(f"Failed to get TTL for session {session_id}: {str(e)}")
            return None

    async def extend_session_ttl(self, session_id: str) -> bool:
        """Extend session TTL by another REDIS_SESSION_TTL period."""
        if not self._initialized or not self.redis_client:
            return False

        try:
            key = f"session:{session_id}"
            await self.redis_client.expire(key, settings.REDIS_SESSION_TTL)
            logger.debug(f"Session {session_id} TTL extended")
            return True

        except Exception as e:
            logger.error(f"Failed to extend TTL for session {session_id}: {str(e)}")
            return False

    async def cleanup_expired_sessions(self, pattern: str = "session:*") -> int:
        """Clean up expired sessions matching pattern. Returns number of deleted sessions."""
        if not self._initialized or not self.redis_client:
            return 0

        try:
            # Get all session keys
            keys = await self.redis_client.keys(pattern)

            if not keys:
                return 0

            # Get TTL for each key
            expired_keys = []
            for key in keys:
                ttl = await self.redis_client.ttl(key)
                if ttl <= 0:  # Expired or doesn't exist
                    expired_keys.append(key)

            # Delete expired keys
            if expired_keys:
                deleted = await self.redis_client.delete(*expired_keys)
                logger.info(f"Cleaned up {deleted} expired sessions")
                return deleted

            return 0

        except Exception as e:
            logger.error(f"Failed to cleanup expired sessions: {str(e)}")
            return 0

    async def get_session_count(self) -> int:
        """Get total number of sessions in Redis."""
        if not self._initialized or not self.redis_client:
            return 0

        try:
            keys = await self.redis_client.keys("session:*")
            return len(keys)

        except Exception as e:
            logger.error(f"Failed to get session count: {str(e)}")
            return 0

    async def close(self):
        """Close Redis connections."""
        if self.redis_client:
            await self.redis_client.close()
        if self.connection_pool:
            await self.connection_pool.disconnect()
        self._initialized = False
        logger.info("Redis session store closed")


# Global instance
_redis_session_store: Optional[RedisSessionStore] = None


async def get_redis_session_store() -> RedisSessionStore:
    """Get singleton Redis session store instance."""
    global _redis_session_store
    if _redis_session_store is None:
        _redis_session_store = RedisSessionStore()
        await _redis_session_store.initialize()
    return _redis_session_store
