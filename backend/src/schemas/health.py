"""Health check response schemas."""

from datetime import datetime
from enum import Enum
from typing import Dict, Optional
from pydantic import BaseModel, Field


class ServiceStatus(str, Enum):
    """Service status enumeration."""
    UP = "up"
    DOWN = "down"
    DEGRADED = "degraded"


class HealthCheck(BaseModel):
    """Health check response model."""
    status: str = Field(..., description="Overall health status", example="healthy")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Health check timestamp")
    version: str = Field(..., description="Service version", example="1.0.0")
    services: Dict[str, ServiceStatus] = Field(..., description="Individual service statuses")

    class Config:
        json_schema_extra = {
            "example": {
                "status": "healthy",
                "timestamp": "2025-01-15T10:30:00Z",
                "version": "1.0.0",
                "services": {
                    "efl_terminal": "up",
                    "cma_cgm": "up",
                    "openai": "up",
                    "twilio": "up",
                    "redis": "up"
                }
            }
        }
