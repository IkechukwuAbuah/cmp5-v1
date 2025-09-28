"""Vessel voyage models for container tracking."""

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class VoyageStatus(str, Enum):
    """Supported voyage lifecycle states."""
    PLANNED = "planned"
    DEPARTED = "departed"
    IN_TRANSIT = "in_transit"
    ARRIVED = "arrived"
    DELAYED = "delayed"


class VesselVoyage(BaseModel):
    """Represents a vessel voyage leg for a shipment."""
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


__all__ = ["VoyageStatus", "VesselVoyage"]
