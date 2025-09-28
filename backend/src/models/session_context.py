"""Session context models supporting conversational state."""

from typing import List, Optional, TYPE_CHECKING

from pydantic import BaseModel, Field

if TYPE_CHECKING:  # pragma: no cover - only for typing
    from src.models.agent import ChannelType


class EntityReference(BaseModel):
    """Reference to a domain entity mentioned in conversation."""
    type: str = Field(..., description="Entity type", example="container")
    id: str = Field(..., description="Entity ID", example="EFLU7896543")
    confidence: float = Field(..., description="Recognition confidence score", ge=0, le=1)


class SessionContext(BaseModel):
    """Mutable conversational context associated with an agent session."""
    currentIntent: Optional[str] = Field(None, description="Current conversation intent")
    activeEntities: List[EntityReference] = Field(default_factory=list, description="Active entities in conversation")
    preferredChannel: Optional["ChannelType"] = Field(None, description="Most recent preferred channel")
    preferredLanguage: Optional[str] = Field(
        None,
        description="Persisted language preference code",
        example="en"
    )
    preferredCulturalContext: Optional[str] = Field(
        None,
        description="Persisted cultural context preference",
        example="nigerian"
    )
    lastResponse: str = Field(..., description="Last assistant response")
    pendingActions: List[str] = Field(default_factory=list, description="Actions awaiting user response")


__all__ = ["EntityReference", "SessionContext"]
