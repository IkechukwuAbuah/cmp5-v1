"""Bill of Lading domain model."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from src.models.vessel_voyage import VesselVoyage


class BillOfLading(BaseModel):
    """Represents a bill of lading for a shipment."""
    id: str = Field(..., description="BL number", example="ABC1234567")
    blNumber: str = Field(..., description="Bill of Lading number", example="ABC1234567")
    vesselVoyage: VesselVoyage = Field(..., description="Transport vessel and voyage")
    origin: str = Field(..., description="Port of origin", example="Lagos")
    destination: str = Field(..., description="Port of destination", example="Ikorodu")
    estimatedArrival: datetime = Field(..., description="ETA at destination port")
    actualArrival: Optional[datetime] = Field(None, description="Actual arrival if available")
    shippingLine: str = Field(..., description="CMA CGM or other carrier", example="CMA CGM")
    agentId: str = Field(..., description="Assigned clearing agent", example="agent_123")


__all__ = ["BillOfLading"]
