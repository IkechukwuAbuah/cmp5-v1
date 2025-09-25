"""Session management schemas."""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field

from src.models.agent import ChannelType, SessionContext, Message


class SessionResponse(BaseModel):
    """Session response model."""
    id: str = Field(..., description="Unique session identifier")
    agentId: str = Field(..., description="Associated agent")
    channel: ChannelType = Field(..., description="Communication channel")
    startTime: datetime = Field(..., description="Session start timestamp")
    context: SessionContext = Field(..., description="Current conversation context")
    messageCount: int = Field(..., description="Number of messages in session")

    class Config:
        json_schema_extra = {
            "example": {
                "id": "sess_123",
                "agentId": "agent_123",
                "channel": "chat",
                "startTime": "2025-01-15T10:30:00Z",
                "context": {
                    "currentIntent": "track_container",
                    "activeEntities": [
                        {
                            "type": "container",
                            "id": "EFLU7896543",
                            "confidence": 0.95
                        }
                    ],
                    "lastResponse": "Container EFLU7896543 is currently at EFL Terminal, Ikorodu.",
                    "pendingActions": ["book_exam"]
                },
                "messageCount": 5
            }
        }


class SessionMessagesResponse(BaseModel):
    """Session messages response model."""
    sessionId: str = Field(..., description="Session identifier")
    messages: List[Message] = Field(..., description="List of messages")
    total: int = Field(..., description="Total number of messages")

    class Config:
        json_schema_extra = {
            "example": {
                "sessionId": "sess_123",
                "messages": [
                    {
                        "id": "msg_1",
                        "type": "user",
                        "content": "Track container EFLU7896543",
                        "timestamp": "2025-01-15T10:30:00Z"
                    },
                    {
                        "id": "msg_2",
                        "type": "assistant",
                        "content": "Container EFLU7896543 is currently at EFL Terminal, Ikorodu. Status: Cleared for exam.",
                        "timestamp": "2025-01-15T10:30:05Z"
                    }
                ],
                "total": 2
            }
        }
