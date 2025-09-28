"""Session management API endpoints."""

import time
from typing import Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status
from src.middleware.auth import get_current_agent
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address

from src.core.config import settings
from src.models.agent import Agent, ChannelType
from src.schemas.error import ErrorResponse
from src.schemas.session import ChannelSwitchRequest, ChannelSwitchResponse, SessionResponse
from src.services.channel_router import ChannelRouterService
from src.services.session_service import SessionService

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)




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



@router.post("/sessions/{sessionId}/channel", response_model=ChannelSwitchResponse)
@limiter.limit("30/minute")
async def switch_session_channel(
    request: Request,
    sessionId: str,
    payload: ChannelSwitchRequest,
    agent: Agent = Depends(get_current_agent)
):
    """Switch a session between voice and chat channels while preserving context."""
    try:
        if not _agent_owns_session(sessionId, agent.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions to switch this session"
            )

        session_service = await SessionService().get_instance()
        await session_service.update_localisation_preferences(
            sessionId,
            agent.id,
            language=getattr(request.state, "language", None),
            cultural_context=getattr(request.state, "cultural_context", None),
        )

        router = await ChannelRouterService().get_instance()
        target_channel = payload.targetChannel

        if target_channel == ChannelType.VOICE:
            routing_result = await router.route_to_voice(
                sessionId, agent.id, payload.contextOverride
            )
        elif target_channel == ChannelType.CHAT:
            routing_result = await router.route_to_chat(
                sessionId, agent.id, payload.voiceContext or {}
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Unsupported target channel"
            )

        return ChannelSwitchResponse(
            sessionId=routing_result.get("sessionId", sessionId),
            channel=ChannelType(routing_result.get("channel", target_channel.value)),
            context=routing_result.get("context", {}),
        )

    except HTTPException:
        raise
    except Exception as exc:
        print(f"Switch session channel error: {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error while switching channel"
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
