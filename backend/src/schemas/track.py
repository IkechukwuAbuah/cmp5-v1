"""Track request and response schemas."""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field

from src.models.container import Container, BillOfLading
from src.models.agent import ChannelType


class TrackRequest(BaseModel):
    """Request model for tracking queries."""
    query: str = Field(..., description="Natural language query for tracking", example="Track container EFLU7896543")
    channel: ChannelType = Field(..., description="Communication channel")
    sessionId: Optional[str] = Field(None, description="Session identifier for conversation context")
    agentId: str = Field(..., description="Agent identifier")

    class Config:
        json_schema_extra = {
            "example": {
                "query": "Track container EFLU7896543",
                "channel": "chat",
                "sessionId": "sess_123",
                "agentId": "agent_123"
            }
        }


class TrackResponse(BaseModel):
    """Response model for tracking queries."""
    sessionId: str = Field(..., description="Unique session identifier", example="sess_123")
    response: str = Field(..., description="Natural language response", example="Container EFLU7896543 is currently at EFL Terminal, Ikorodu. Status: Cleared for exam.")
    containers: List[Container] = Field(default_factory=list, description="Associated containers")
    billOfLadings: List[BillOfLading] = Field(default_factory=list, description="Associated bills of lading")
    nextStep: str = Field(..., description="Next action for user", example="You may now book a customs examination.")
    followUp: bool = Field(..., description="Whether this response expects user follow-up", example=True)
    confidence: float = Field(..., description="Response confidence score", ge=0, le=1, example=0.95)
    metadata: Optional[dict] = Field(None, description="Additional response metadata")

    class Config:
        json_schema_extra = {
            "example": {
                "sessionId": "sess_123",
                "response": "Container EFLU7896543 is currently at EFL Terminal, Ikorodu. Status: Cleared for exam.",
                "containers": [],
                "billOfLadings": [],
                "nextStep": "You may now book a customs examination.",
                "followUp": True,
                "confidence": 0.95,
                "metadata": {
                    "processing_time_ms": 450,
                    "data_sources": ["efl_terminal", "cma_cgm"]
                }
            }
        }
