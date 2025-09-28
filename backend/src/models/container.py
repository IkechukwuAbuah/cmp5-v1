"""Container model and related schemas."""

from datetime import datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field, validator

from src.models.bill_of_lading import BillOfLading
from src.models.container_milestone import ContainerMilestone
from src.models.terminal_location import TerminalLocation
from src.models.vessel_voyage import VesselVoyage


class ContainerStatus(str, Enum):
    """Container status enumeration."""
    IN_TRANSIT = "in_transit"
    AT_TERMINAL = "at_terminal"
    DISCHARGED = "discharged"
    CLEARED_FOR_EXAM = "cleared_for_exam"
    UNDER_EXAM = "under_exam"
    RELEASED = "released"
    DELIVERED = "delivered"


class Container(BaseModel):
    """Container model."""
    id: str = Field(..., description="Unique container identifier", example="EFLU7896543")
    containerNumber: str = Field(..., description="ISO container number", example="EFLU7896543")
    isoCode: str = Field(..., description="Container size/type code", example="45G1")
    status: ContainerStatus = Field(..., description="Current status")
    location: TerminalLocation = Field(..., description="Current physical location")
    billOfLading: BillOfLading = Field(..., description="Associated BL reference")
    agentId: str = Field(..., description="Assigned clearing agent", example="agent_123")
    milestones: List[ContainerMilestone] = Field(default_factory=list, description="Historical status changes")
    lastUpdated: datetime = Field(..., description="Last status update timestamp")
    nextStep: str = Field(..., description="Next action required", example="Awaiting exam booking")

    @validator('containerNumber')
    def validate_container_number(cls, v):
        """Validate ISO 6346 container number format."""
        # Basic validation - should be 11 characters, starting with 4 letters
        if not (len(v) == 11 and v[:4].isalpha()):
            raise ValueError('Container number must follow ISO 6346 format')
        return v.upper()

    @validator('isoCode')
    def validate_iso_code(cls, v):
        """Validate ISO container type code."""
        # Basic validation - should be 4 characters (2 letters + 2 numbers)
        if not (len(v) == 4 and v[:2].isalpha() and v[2:].isdigit()):
            raise ValueError('ISO code must be 4 characters (2 letters + 2 numbers)')
        return v.upper()


class ContainerResponse(BaseModel):
    """Container response model for API responses."""
    id: str
    containerNumber: str
    isoCode: str
    status: ContainerStatus
    location: TerminalLocation
    billOfLading: BillOfLading
    agentId: str
    lastUpdated: datetime
    nextStep: str
    milestoneCount: int = Field(description="Number of milestone events")


class BillOfLadingResponse(BaseModel):
    """Bill of Lading response model for API responses."""
    id: str
    blNumber: str
    vesselVoyage: VesselVoyage
    origin: str
    destination: str
    estimatedArrival: datetime
    actualArrival: Optional[datetime]
    shippingLine: str
    agentId: str
    containerCount: int = Field(description="Number of associated containers")
