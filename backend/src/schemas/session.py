"""Session management schemas."""

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from src.models.agent import ChannelType
from src.models.agent_session import Message
from src.models.session_context import SessionContext


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
                    "pendingActions": ["book_exam"],
                    "preferredChannel": "chat"
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



class ChannelSwitchRequest(BaseModel):
    """Payload for switching a session channel."""
    targetChannel: ChannelType = Field(..., description="Channel to switch to")
    contextOverride: Optional[Dict[str, Any]] = Field(
        None, description="Additional context to seed the target channel"
    )
    voiceContext: Optional[Dict[str, Any]] = Field(
        None, description="Voice context payload when moving from voice to chat"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "targetChannel": "voice",
                "contextOverride": {
                    "current_intent": "track_container",
                    "context_variables": {"phone_number": "+2347012345678"}
                }
            }
        }


class ChannelSwitchResponse(BaseModel):
    """Response returned after switching a session channel."""
    sessionId: str = Field(..., description="Session identifier after switch")
    channel: ChannelType = Field(..., description="Active channel")
    context: Dict[str, Any] = Field(
        default_factory=dict,
        description="Channel-specific context snapshot used for continuity",
    )

    class Config:
        json_schema_extra = {
            "example": {
                "sessionId": "sess_123",
                "channel": "voice",
                "context": {
                    "current_intent": "track_container",
                    "recent_entities": [
                        {"type": "container", "id": "EFLU7896543", "confidence": 0.95}
                    ],
                    "pending_clarifications": []
                }
            }
        }
