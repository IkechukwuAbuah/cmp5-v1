"""Container milestone tracking models."""

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field

from src.models.terminal_location import TerminalLocation


class DataSource(str, Enum):
    """Enumerates upstream systems supplying milestone data."""
    EFL_TERMINAL = "efl_terminal"
    CMA_CGM = "cma_cgm"
    TOS = "tos"


class EventType(str, Enum):
    """Container event categories emitted by logistics systems."""
    LOADED = "loaded"
    DISCHARGED = "discharged"
    GATE_IN = "gate_in"
    GATE_OUT = "gate_out"
    CUSTOMS_EXAM = "customs_exam"
    RELEASED = "released"
    DELIVERED = "delivered"
    TRANSSHIPMENT = "transshipment"


class ContainerMilestone(BaseModel):
    """Represents a single event in a container's journey."""
    id: str = Field(..., description="Unique milestone identifier", example="mil_123")
    containerId: str = Field(..., description="Associated container", example="EFLU7896543")
    eventType: EventType = Field(..., description="Type of event")
    location: TerminalLocation = Field(..., description="Location where event occurred")
    timestamp: datetime = Field(..., description="When the event happened")
    description: str = Field(..., description="Human-readable description", example="Container discharged from vessel")
    source: DataSource = Field(..., description="EFL Terminal or CMA CGM")
    metadata: Optional[dict] = Field(None, description="Additional event-specific data")


__all__ = ["DataSource", "EventType", "ContainerMilestone"]
