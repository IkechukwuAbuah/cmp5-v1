"""Terminal location domain models."""

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class LocationType(str, Enum):
    """Enumeration of supported terminal location types."""
    YARD = "yard"
    GATE_IN = "gate_in"
    GATE_OUT = "gate_out"
    WAREHOUSE = "warehouse"
    EXAM_AREA = "exam_area"


class Coordinates(BaseModel):
    """GPS coordinate pair for a terminal location."""
    latitude: float = Field(..., description="Latitude coordinate", example=6.4474)
    longitude: float = Field(..., description="Longitude coordinate", example=3.3903)


class TerminalLocation(BaseModel):
    """Physical location inside an EFL terminal."""
    id: str = Field(..., description="Unique location identifier", example="loc_123")
    name: str = Field(..., description="Human-readable name", example="Yard A1")
    type: LocationType = Field(..., description="Location type")
    coordinates: Optional[Coordinates] = Field(None, description="GPS coordinates if available")
    terminalId: str = Field(..., description="Associated terminal", example="efl_terminal")
    isActive: bool = Field(..., description="Whether location is operational", example=True)


__all__ = ["LocationType", "Coordinates", "TerminalLocation"]
