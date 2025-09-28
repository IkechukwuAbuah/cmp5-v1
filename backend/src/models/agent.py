"""Agent/User model and related schemas."""

from datetime import datetime
from enum import Enum
from typing import List, Optional, TYPE_CHECKING

from pydantic import BaseModel, Field, validator

if TYPE_CHECKING:  # pragma: no cover - typing helpers
    from src.models.agent_session import AgentSession, Message
    from src.models.session_context import SessionContext


class AgentType(str, Enum):
    """Agent type enumeration."""
    CLEARING = "clearing"
    SHIPPING = "shipping"
    TERMINAL = "terminal"
    ADMIN = "admin"


class ChannelType(str, Enum):
    """Channel type enumeration."""
    VOICE = "voice"
    CHAT = "chat"
    API = "api"


class ContactInfo(BaseModel):
    """Contact information model."""
    phone: Optional[str] = Field(None, description="Phone number", example="+234-123-4567")
    email: Optional[str] = Field(None, description="Email address", example="agent@efl.com")
    companyName: str = Field(..., description="Company name", example="EFL Clearing Agency")


class Permission(BaseModel):
    """Permission model."""
    resource: str = Field(..., description="Resource type", example="container")
    actions: List[str] = Field(..., description="Allowed actions", example=["read", "track"])
    conditions: Optional[List[str]] = Field(None, description="Optional conditions for access")


class Agent(BaseModel):
    """Agent/User model."""
    id: str = Field(..., description="Unique agent identifier", example="agent_123")
    name: str = Field(..., description="Agent company name", example="EFL Clearing Agency")
    type: AgentType = Field(..., description="Agent type")
    contactInfo: ContactInfo = Field(..., description="Contact information")
    permissions: List[Permission] = Field(default_factory=list, description="Role-based permissions")
    sessionHistory: List["AgentSession"] = Field(default_factory=list, description="Session history")
    createdAt: datetime = Field(default_factory=datetime.utcnow, description="Account creation timestamp")
    lastLogin: Optional[datetime] = Field(None, description="Last login timestamp")
    isActive: bool = Field(default=True, description="Whether agent account is active")

    @validator('name')
    def validate_name(cls, v):
        """Validate agent name is not empty."""
        if not v.strip():
            raise ValueError('Agent name cannot be empty')
        return v.strip()

    def has_permission(self, resource: str, action: str) -> bool:
        """Check if agent has permission for resource and action."""
        for permission in self.permissions:
            if permission.resource == resource and action in permission.actions:
                return True
        return False

    def can_access_container(self, container_id: str) -> bool:
        """Check if agent can access a specific container."""
        # This would typically check against a database or external system
        # For now, we'll implement basic logic
        return self.has_permission("container", "read")

    def can_access_bl(self, bl_number: str) -> bool:
        """Check if agent can access a specific bill of lading."""
        # This would typically check against a database or external system
        # For now, we'll implement basic logic
        return self.has_permission("bl", "read")


from src.models.agent_session import AgentSession, Message, SessionStatus
from src.models.session_context import SessionContext

SessionContext.model_rebuild(_types_namespace={"ChannelType": ChannelType})

AgentSession.model_rebuild(
    _types_namespace={
        "ChannelType": ChannelType,
        "SessionContext": SessionContext,
        "Message": Message,
        "SessionStatus": SessionStatus,
    }
)

Agent.model_rebuild(
    _types_namespace={
        "AgentSession": AgentSession,
        "SessionContext": SessionContext,
        "Message": Message,
    }
)


__all__ = [
    "AgentType",
    "ChannelType",
    "ContactInfo",
    "Permission",
    "Agent",
]
