"""Agent/User model and related schemas."""

from datetime import datetime
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field, validator


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


class SessionStatus(str, Enum):
    """Session status enumeration."""
    ACTIVE = "active"
    COMPLETED = "completed"
    EXPIRED = "expired"
    TIMEOUT = "timeout"


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


class EntityReference(BaseModel):
    """Entity reference model."""
    type: str = Field(..., description="Entity type", example="container")
    id: str = Field(..., description="Entity ID", example="EFLU7896543")
    confidence: float = Field(..., description="Recognition confidence score", ge=0, le=1)


class SessionContext(BaseModel):
    """Session context model."""
    currentIntent: Optional[str] = Field(None, description="Current conversation intent")
    activeEntities: List[EntityReference] = Field(default_factory=list, description="Active entities in conversation")
    lastResponse: str = Field(..., description="Last assistant response")
    pendingActions: List[str] = Field(default_factory=list, description="Actions awaiting user response")


class Message(BaseModel):
    """Message model."""
    id: str = Field(..., description="Unique message identifier")
    type: str = Field(..., description="Message type (user/assistant)")
    content: str = Field(..., description="Message content")
    timestamp: datetime = Field(..., description="Message timestamp")
    metadata: Optional[dict] = Field(None, description="Additional message metadata")


class AgentSession(BaseModel):
    """Agent session model."""
    id: str = Field(..., description="Unique session identifier", example="sess_123")
    agentId: str = Field(..., description="Associated agent", example="agent_123")
    channel: ChannelType = Field(..., description="Communication channel")
    startTime: datetime = Field(..., description="Session start timestamp")
    endTime: Optional[datetime] = Field(None, description="Session end timestamp")
    conversationHistory: List[Message] = Field(default_factory=list, description="All messages in session")
    context: SessionContext = Field(..., description="Current conversation context")
    status: SessionStatus = Field(default=SessionStatus.ACTIVE, description="Session status")


class Agent(BaseModel):
    """Agent/User model."""
    id: str = Field(..., description="Unique agent identifier", example="agent_123")
    name: str = Field(..., description="Agent company name", example="EFL Clearing Agency")
    type: AgentType = Field(..., description="Agent type")
    contactInfo: ContactInfo = Field(..., description="Contact information")
    permissions: List[Permission] = Field(default_factory=list, description="Role-based permissions")
    sessionHistory: List[AgentSession] = Field(default_factory=list, description="Session history")
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
