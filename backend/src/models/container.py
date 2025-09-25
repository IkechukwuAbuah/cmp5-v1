"""Container model and related schemas."""

from datetime import datetime
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field, validator


class ContainerStatus(str, Enum):
    """Container status enumeration."""
    IN_TRANSIT = "in_transit"
    AT_TERMINAL = "at_terminal"
    DISCHARGED = "discharged"
    CLEARED_FOR_EXAM = "cleared_for_exam"
    UNDER_EXAM = "under_exam"
    RELEASED = "released"
    DELIVERED = "delivered"


class DataSource(str, Enum):
    """Data source enumeration."""
    EFL_TERMINAL = "efl_terminal"
    CMA_CGM = "cma_cgm"
    TOS = "tos"


class EventType(str, Enum):
    """Container event types."""
    LOADED = "loaded"
    DISCHARGED = "discharged"
    GATE_IN = "gate_in"
    GATE_OUT = "gate_out"
    CUSTOMS_EXAM = "customs_exam"
    RELEASED = "released"
    DELIVERED = "delivered"
    TRANSSHIPMENT = "transshipment"


class LocationType(str, Enum):
    """Location type enumeration."""
    YARD = "yard"
    GATE_IN = "gate_in"
    GATE_OUT = "gate_out"
    WAREHOUSE = "warehouse"
    EXAM_AREA = "exam_area"


class VoyageStatus(str, Enum):
    """Voyage status enumeration."""
    PLANNED = "planned"
    DEPARTED = "departed"
    IN_TRANSIT = "in_transit"
    ARRIVED = "arrived"
    DELAYED = "delayed"


class Coordinates(BaseModel):
    """GPS coordinates model."""
    latitude: float = Field(..., description="Latitude coordinate", example=6.4474)
    longitude: float = Field(..., description="Longitude coordinate", example=3.3903)


class TerminalLocation(BaseModel):
    """Terminal location model."""
    id: str = Field(..., description="Unique location identifier", example="loc_123")
    name: str = Field(..., description="Human-readable name", example="Yard A1")
    type: LocationType = Field(..., description="Location type")
    coordinates: Optional[Coordinates] = Field(None, description="GPS coordinates if available")
    terminalId: str = Field(..., description="Associated terminal", example="efl_terminal")
    isActive: bool = Field(..., description="Whether location is operational", example=True)


class VesselVoyage(BaseModel):
    """Vessel voyage model."""
    id: str = Field(..., description="Unique voyage identifier", example="voy_123")
    vesselName: str = Field(..., description="Name of the vessel", example="Marco Polo")
    voyageNumber: str = Field(..., description="Voyage reference number", example="12345")
    carrier: str = Field(..., description="CMA CGM or other", example="CMA CGM")
    originPort: str = Field(..., description="Port of departure", example="Lagos Port")
    destinationPort: str = Field(..., description="Port of arrival", example="EFL Terminal, Ikorodu")
    estimatedDeparture: datetime = Field(..., description="ETD from origin")
    estimatedArrival: datetime = Field(..., description="ETA at destination")
    actualDeparture: Optional[datetime] = Field(None, description="Actual departure if available")
    actualArrival: Optional[datetime] = Field(None, description="Actual arrival if available")
    status: VoyageStatus = Field(..., description="Current voyage status")


class ContainerMilestone(BaseModel):
    """Container milestone/event model."""
    id: str = Field(..., description="Unique milestone identifier", example="mil_123")
    containerId: str = Field(..., description="Associated container", example="EFLU7896543")
    eventType: EventType = Field(..., description="Type of event")
    location: TerminalLocation = Field(..., description="Location where event occurred")
    timestamp: datetime = Field(..., description="When the event happened")
    description: str = Field(..., description="Human-readable description", example="Container discharged from vessel")
    source: DataSource = Field(..., description="EFL Terminal or CMA CGM")
    metadata: Optional[dict] = Field(None, description="Additional event-specific data")


class BillOfLading(BaseModel):
    """Bill of Lading model."""
    id: str = Field(..., description="BL number", example="ABC1234567")
    blNumber: str = Field(..., description="Bill of Lading number", example="ABC1234567")
    vesselVoyage: VesselVoyage = Field(..., description="Transport vessel and voyage")
    origin: str = Field(..., description="Port of origin", example="Lagos")
    destination: str = Field(..., description="Port of destination", example="Ikorodu")
    estimatedArrival: datetime = Field(..., description="ETA at destination port")
    actualArrival: Optional[datetime] = Field(None, description="Actual arrival if available")
    shippingLine: str = Field(..., description="CMA CGM or other carrier", example="CMA CGM")
    agentId: str = Field(..., description="Assigned clearing agent", example="agent_123")


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
