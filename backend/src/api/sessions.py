"""Session management API endpoints."""

import time
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address

from src.core.config import settings
from src.models.agent import Agent
from src.schemas.error import ErrorResponse
from src.schemas.session import SessionResponse

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


@router.get("/sessions/{sessionId}", response_model=SessionResponse)
@limiter.limit("60/minute")
async def get_session(
    request: Request,
    sessionId: str,
    agent: Agent = Depends(get_current_agent)
):
    """Get session information by session ID."""
    try:
        # Validate agent permissions
        # This would typically check if agent owns the session
        if not _agent_owns_session(sessionId, agent.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions to access this session"
            )

        # Query session data (mock implementation)
        session = await _get_session_from_storage(sessionId)

        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Session with ID {sessionId} not found"
            )

        return SessionResponse(
            id=session.id,
            agentId=session.agentId,
            channel=session.channel,
            startTime=session.startTime,
            context=session.context,
            messageCount=len(session.conversationHistory)
        )

    except HTTPException:
        raise
    except Exception as e:
        # Log error and return appropriate error response
        print(f"Get session error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error while retrieving session"
        )


def _agent_owns_session(session_id: str, agent_id: str) -> bool:
    """Check if agent owns the session."""
    # This would typically check session ownership in Redis/database
    # For now, we'll assume session IDs contain agent ID
    return agent_id in session_id


async def _get_session_from_storage(session_id: str):
    """Get session data from storage (mock implementation)."""
    # This would typically query Redis for session data
    # For now, we'll return None to indicate session not found
    return None
