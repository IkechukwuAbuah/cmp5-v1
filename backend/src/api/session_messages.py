"""Session messages API endpoints."""

import time
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status, Query
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address

from src.core.config import settings
from src.models.agent import Agent, Message
from src.schemas.error import ErrorResponse
from src.schemas.session import SessionMessagesResponse

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)


def get_current_agent(agent_id: str) -> Agent:
    """Get current agent (placeholder for authentication)."""
    # This would typically verify JWT token and return authenticated agent
    # For now, we'll create a mock agent
    return Agent(
        id=agent_id,
        name="Mock Agent",
        type="clearing",
        contactInfo={
            "phone": "+234-123-4567",
            "email": "agent@efl.com",
            "companyName": "Mock Agency"
        }
    )


@router.get("/sessions/{sessionId}/messages", response_model=SessionMessagesResponse)
@limiter.limit("60/minute")
async def get_session_messages(
    request: Request,
    sessionId: str,
    limit: int = Query(50, ge=1, le=100, description="Maximum number of messages to return"),
    agent: Agent = Depends(get_current_agent)
):
    """Get session message history with pagination."""
    try:
        # Validate agent permissions
        if not _agent_owns_session(sessionId, agent.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions to access this session"
            )

        # Query message data (mock implementation)
        messages, total = await _get_session_messages(sessionId, limit)

        return SessionMessagesResponse(
            sessionId=sessionId,
            messages=messages,
            total=total
        )

    except HTTPException:
        raise
    except Exception as e:
        # Log error and return appropriate error response
        print(f"Get session messages error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error while retrieving session messages"
        )


def _agent_owns_session(session_id: str, agent_id: str) -> bool:
    """Check if agent owns the session."""
    # This would typically check session ownership in Redis/database
    # For now, we'll assume session IDs contain agent ID
    return agent_id in session_id


async def _get_session_messages(session_id: str, limit: int) -> tuple[List[Message], int]:
    """Get session messages with pagination."""
    # Mock message data
    messages = [
        Message(
            id=f"msg_{i}",
            type="user" if i % 2 == 0 else "assistant",
            content=f"Mock message {i}",
            timestamp=time.time() - (100 - i) * 60,  # Spread over last 100 minutes
            metadata={}
        )
        for i in range(min(10, limit))  # Mock 10 messages
    ]

    return messages, len(messages)
