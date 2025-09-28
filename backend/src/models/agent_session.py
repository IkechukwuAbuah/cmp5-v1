"""Agent session domain models."""

from datetime import datetime
from enum import Enum
from typing import List, Optional, TYPE_CHECKING

from pydantic import BaseModel, Field

from src.models.session_context import SessionContext

if TYPE_CHECKING:  # pragma: no cover - typing helpers
    from src.models.agent import ChannelType


class SessionStatus(str, Enum):
    """Lifecycle states for an agent session."""
    ACTIVE = "active"
    COMPLETED = "completed"
    EXPIRED = "expired"
    TIMEOUT = "timeout"


class Message(BaseModel):
    """Single message exchanged within an agent session."""
    id: str = Field(..., description="Unique message identifier")
    type: str = Field(..., description="Message type (user/assistant)")
    content: str = Field(..., description="Message content")
    timestamp: datetime = Field(..., description="Message timestamp")
    metadata: Optional[dict] = Field(None, description="Additional message metadata")


class AgentSession(BaseModel):
    """Conversation channel session for an agent."""
    id: str = Field(..., description="Unique session identifier", example="sess_123")
    agentId: str = Field(..., description="Associated agent", example="agent_123")
    channel: "ChannelType" = Field(..., description="Communication channel")
    startTime: datetime = Field(..., description="Session start timestamp")
    endTime: Optional[datetime] = Field(None, description="Session end timestamp")
    conversationHistory: List[Message] = Field(default_factory=list, description="All messages in session")
    context: SessionContext = Field(..., description="Current conversation context")
    status: SessionStatus = Field(default=SessionStatus.ACTIVE, description="Session status")


__all__ = ["SessionStatus", "Message", "AgentSession"]
