"""Error response schemas."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class ErrorResponse(BaseModel):
    """Error response model."""
    error: str = Field(..., description="Error code", example="CONTAINER_NOT_FOUND")
    message: str = Field(..., description="Human-readable error message", example="Container with ID EFLU7896543 not found")
    details: Optional[dict] = Field(None, description="Additional error details")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Error timestamp")

    class Config:
        json_schema_extra = {
            "example": {
                "error": "CONTAINER_NOT_FOUND",
                "message": "Container with ID EFLU7896543 not found",
                "details": {
                    "containerId": "EFLU7896543",
                    "agentId": "agent_123"
                },
                "timestamp": "2025-01-15T10:30:00Z"
            }
        }
