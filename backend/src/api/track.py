"""Track API endpoint for natural language container tracking."""

import time
import uuid
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status
from src.middleware.auth import get_current_agent
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address

from src.core.config import settings
from src.models.agent import Agent, ChannelType
from src.models.agent_session import AgentSession, Message, SessionStatus
from src.models.session_context import SessionContext
from src.models.container import Container, ContainerStatus
from src.services.track_service import TrackService
from src.services.response_service import ResponseService
from src.services.session_service import SessionService
from src.schemas.error import ErrorResponse
from src.schemas.track import TrackRequest, TrackResponse
from src.localisation.cultural_messages import ErrorContext
from src.lib.error_utils import build_error_detail

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)




@router.post("/track", response_model=TrackResponse)
# @limiter.limit("30/minute")  # Temporarily disabled for debugging
async def track_container(
    payload: TrackRequest,
    http_request: Request,
    agent: Agent = Depends(get_current_agent)
):
    """Track container or shipment using natural language query."""
    start_time = time.time()

    try:

        # Validate agent permissions
        if not agent.has_permission("container", "read"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=build_error_detail(
                    "PERMISSION_DENIED",
                    ErrorContext.PERMISSION_DENIED,
                    agent_id=agent.id,
                ),
            )

        # Initialize services
        track_service = await TrackService().get_instance()
        response_service = await ResponseService().get_instance()
        session_service = await SessionService().get_instance()

        # Create or update session
        session: Optional[AgentSession] = None
        if payload.sessionId:
            session = await session_service.get_session(payload.sessionId, agent.id)

        if not session:
            session = await session_service.create_session(agent.id, payload.channel)

        language_pref = getattr(http_request.state, "language", None)
        cultural_pref = getattr(http_request.state, "cultural_context", None)
        await session_service.update_localisation_preferences(
            session.id,
            agent.id,
            language=language_pref,
            cultural_context=cultural_pref,
        )

        from src.models.agent_session import Message
        await session_service.add_message(
            session.id,
            Message(
                id=str(uuid.uuid4()),
                type="user",
                content=payload.query,
                timestamp=datetime.utcnow()
            )
        )

        # Process natural language query
        result = await track_service.process_natural_language_query(payload.query, agent)

        containers = result.get("containers", [])
        bill_of_ladings = result.get("bill_of_ladings", [])

        # Generate natural language response
        response_text = response_service.format_tracking_response(
            payload.query,
            containers,
            bill_of_ladings,
            payload.channel
        )

        # Determine next step
        next_step = track_service.determine_next_step(containers)

        # Calculate confidence and metadata
        confidence = _calculate_confidence(containers, bill_of_ladings)
        metadata = {
            "processing_time_ms": int((time.time() - start_time) * 1000),
            "agent_id": agent.id,
            "channel": payload.channel,
            "query_entities": result.get("entities", {})
        }

        # Add assistant response to session
        await session_service.add_message(
            session.id,
            Message(
                id=str(uuid.uuid4()),
                type="assistant",
                content=response_text,
                timestamp=datetime.utcnow()
            )
        )

        return TrackResponse(
            sessionId=session.id,
            response=response_text,
            containers=containers,
            billOfLadings=bill_of_ladings,
            nextStep=next_step,
            followUp=_requires_follow_up(containers),
            confidence=confidence,
            metadata=metadata
        )

    except HTTPException:
        raise
    except Exception as e:
        # Log error and return appropriate error response
        print(f"Track endpoint error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=build_error_detail(
                "SYSTEM_UNAVAILABLE",
                ErrorContext.SYSTEM_UNAVAILABLE,
                operation="track_container",
                query=request.query,
            ),
        )


def _calculate_confidence(containers: List[Container], bill_of_ladings: List) -> float:
    """Calculate response confidence score."""
    if containers:
        return 0.95  # High confidence for direct container matches
    elif bill_of_ladings:
        return 0.85  # Medium confidence for BL matches
    else:
        return 0.0   # No confidence if no matches found


def _requires_follow_up(containers: List[Container]) -> bool:
    """Determine if response requires user follow-up."""
    if not containers:
        return True  # Need clarification if no containers found

    container = containers[0]
    # Require follow-up if container needs action
    return container.status in [ContainerStatus.AT_TERMINAL, ContainerStatus.CLEARED_FOR_EXAM]
