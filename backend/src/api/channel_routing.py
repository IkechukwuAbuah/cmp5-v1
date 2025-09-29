"""Multi-channel routing API endpoints for EFL Agent Assistant."""

import logging
from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Request, Depends, BackgroundTasks
from pydantic import BaseModel

from src.models.agent import Agent, ChannelType
from src.services.channel_router import ChannelRouterService
from src.services.session_service import SessionService
from src.middleware.auth import get_current_agent

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/channel-routing", tags=["channel-routing"])


class ChannelSwitchRequest(BaseModel):
    """Request model for channel switching."""
    session_id: str
    target_channel: ChannelType
    context_override: Optional[Dict[str, Any]] = None
    preserve_history: bool = True


class ChannelSwitchResponse(BaseModel):
    """Response model for channel switching."""
    success: bool
    session_id: str
    channel: ChannelType
    context: Dict[str, Any]
    message: str


class ChannelPreferenceRequest(BaseModel):
    """Request model for setting channel preferences."""
    preferred_channel: ChannelType
    context: Optional[str] = None  # e.g., "urgent", "complex_query", "general"


class SessionMergeRequest(BaseModel):
    """Request model for merging sessions across channels."""
    primary_session_id: str
    secondary_session_id: str
    merge_strategy: str = "preserve_primary"  # or "interleave", "merge_context"


@router.post("/switch", response_model=ChannelSwitchResponse)
async def switch_channel(
    request: ChannelSwitchRequest,
    agent: Agent = Depends(get_current_agent),
    background_tasks: BackgroundTasks = None
) -> ChannelSwitchResponse:
    """Switch session to a different channel while preserving context."""
    try:
        channel_router = await ChannelRouterService().get_instance()
        session_service = await SessionService().get_instance()

        # Verify session exists and belongs to agent
        session = await session_service.get_session(request.session_id, agent.id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")

        # Perform channel switch based on target channel
        if request.target_channel == ChannelType.VOICE:
            result = await channel_router.route_to_voice(
                session_id=request.session_id,
                agent_id=agent.id,
                context_override=request.context_override
            )
            context = result
        elif request.target_channel == ChannelType.CHAT:
            # Get current voice context if switching from voice
            voice_context = None
            if session.channel == ChannelType.VOICE:
                voice_context = session.context.__dict__
            
            result = await channel_router.route_to_chat(
                session_id=request.session_id,
                agent_id=agent.id,
                voice_context=voice_context
            )
            context = result
        else:
            raise HTTPException(status_code=400, detail="Unsupported target channel")

        # Update channel preference learning in background
        if background_tasks:
            background_tasks.add_task(
                _learn_channel_preference,
                agent.id,
                session.channel,
                request.target_channel,
                session.context.currentIntent
            )

        return ChannelSwitchResponse(
            success=True,
            session_id=request.session_id,
            channel=request.target_channel,
            context=context,
            message=f"Successfully switched to {request.target_channel.value} channel"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error switching channel for session {request.session_id}: {e}")
        raise HTTPException(status_code=500, detail="Error switching channel")


@router.post("/merge-sessions")
async def merge_sessions(
    request: SessionMergeRequest,
    agent: Agent = Depends(get_current_agent)
) -> Dict[str, Any]:
    """Merge two sessions from different channels for the same user."""
    try:
        session_service = await SessionService().get_instance()
        channel_router = await ChannelRouterService().get_instance()

        # Get both sessions
        primary_session = await session_service.get_session(request.primary_session_id, agent.id)
        secondary_session = await session_service.get_session(request.secondary_session_id, agent.id)

        if not primary_session or not secondary_session:
            raise HTTPException(status_code=404, detail="One or both sessions not found")

        # Ensure sessions are from different channels
        if primary_session.channel == secondary_session.channel:
            raise HTTPException(status_code=400, detail="Cannot merge sessions from the same channel")

        # Merge based on strategy
        merged_context = await _merge_session_contexts(
            primary_session, secondary_session, request.merge_strategy
        )

        # Update primary session with merged context
        await session_service.update_session_context(request.primary_session_id, merged_context)

        # End secondary session
        await session_service.end_session(request.secondary_session_id, agent.id)

        return {
            "success": True,
            "merged_session_id": request.primary_session_id,
            "merged_context": merged_context.__dict__,
            "message": f"Successfully merged sessions using {request.merge_strategy} strategy"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error merging sessions: {e}")
        raise HTTPException(status_code=500, detail="Error merging sessions")


@router.post("/set-preference")
async def set_channel_preference(
    request: ChannelPreferenceRequest,
    agent: Agent = Depends(get_current_agent)
) -> Dict[str, Any]:
    """Set channel preference for an agent."""
    try:
        # Store preference (in a real implementation, this would go to a database)
        preference_key = f"channel_preference:{agent.id}"
        if request.context:
            preference_key += f":{request.context}"

        # For now, we'll just log the preference
        # In a full implementation, this would be stored in Redis or database
        logger.info(f"Setting channel preference for agent {agent.id}: {request.preferred_channel.value} (context: {request.context})")

        return {
            "success": True,
            "agent_id": agent.id,
            "preferred_channel": request.preferred_channel.value,
            "context": request.context,
            "message": "Channel preference updated successfully"
        }

    except Exception as e:
        logger.error(f"Error setting channel preference: {e}")
        raise HTTPException(status_code=500, detail="Error setting channel preference")


@router.get("/preference")
async def get_channel_preference(
    context: Optional[str] = None,
    agent: Agent = Depends(get_current_agent)
) -> Dict[str, Any]:
    """Get channel preference for an agent."""
    try:
        # In a real implementation, this would query the database
        # For now, we'll return a default preference based on agent type
        default_preference = _get_default_channel_preference(agent, context)

        return {
            "agent_id": agent.id,
            "preferred_channel": default_preference.value,
            "context": context,
            "confidence": 0.8,  # Confidence in the preference
            "learned": False  # Whether this was learned from user behavior
        }

    except Exception as e:
        logger.error(f"Error getting channel preference: {e}")
        raise HTTPException(status_code=500, detail="Error getting channel preference")


@router.get("/session/{session_id}/channels")
async def get_session_channel_history(
    session_id: str,
    agent: Agent = Depends(get_current_agent)
) -> Dict[str, Any]:
    """Get channel switch history for a session."""
    try:
        session_service = await SessionService().get_instance()
        session = await session_service.get_session(session_id, agent.id)

        if not session:
            raise HTTPException(status_code=404, detail="Session not found")

        # In a real implementation, this would track channel switches
        # For now, return current channel info
        return {
            "session_id": session_id,
            "current_channel": session.channel.value,
            "channel_history": [
                {
                    "channel": session.channel.value,
                    "start_time": session.startTime.isoformat(),
                    "end_time": session.endTime.isoformat() if session.endTime else None,
                    "message_count": len(session.conversationHistory)
                }
            ],
            "total_switches": 0  # Would be calculated from history
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting session channel history: {e}")
        raise HTTPException(status_code=500, detail="Error getting channel history")


@router.get("/stats")
async def get_channel_routing_stats(
    agent: Agent = Depends(get_current_agent)
) -> Dict[str, Any]:
    """Get channel routing statistics for an agent."""
    try:
        # In a real implementation, this would query analytics data
        return {
            "agent_id": agent.id,
            "total_sessions": 0,
            "channel_distribution": {
                "voice": 0,
                "chat": 0
            },
            "switch_count": 0,
            "most_common_switch": "chat_to_voice",
            "average_session_duration": {
                "voice": 0,
                "chat": 0
            }
        }

    except Exception as e:
        logger.error(f"Error getting channel routing stats: {e}")
        raise HTTPException(status_code=500, detail="Error getting routing stats")


async def _learn_channel_preference(
    agent_id: str,
    from_channel: ChannelType,
    to_channel: ChannelType,
    intent: Optional[str]
) -> None:
    """Learn channel preferences based on user behavior."""
    try:
        # This would update machine learning models or preference weights
        # For now, just log the learning event
        logger.info(f"Learning: Agent {agent_id} switched from {from_channel.value} to {to_channel.value} for intent '{intent}'")

        # In a real implementation:
        # 1. Update preference weights in database
        # 2. Train/update ML models for preference prediction
        # 3. Analyze patterns for automatic channel suggestions

    except Exception as e:
        logger.error(f"Error learning channel preference: {e}")


async def _merge_session_contexts(primary_session, secondary_session, strategy: str):
    """Merge contexts from two sessions based on strategy."""
    from src.models.agent import SessionContext

    if strategy == "preserve_primary":
        # Keep primary context, add secondary entities
        merged_context = primary_session.context
        merged_context.activeEntities.extend(secondary_session.context.activeEntities)
        
        # Deduplicate entities
        seen = set()
        unique_entities = []
        for entity in merged_context.activeEntities:
            key = (entity.type, entity.id)
            if key not in seen:
                seen.add(key)
                unique_entities.append(entity)
        merged_context.activeEntities = unique_entities[-10:]  # Keep last 10

    elif strategy == "merge_context":
        # Merge all context elements intelligently
        merged_context = SessionContext(
            currentIntent=primary_session.context.currentIntent or secondary_session.context.currentIntent,
            activeEntities=primary_session.context.activeEntities + secondary_session.context.activeEntities,
            lastResponse=primary_session.context.lastResponse or secondary_session.context.lastResponse,
            pendingActions=list(set(primary_session.context.pendingActions + secondary_session.context.pendingActions))
        )

    else:  # interleave
        # Interleave based on timestamps (simplified)
        merged_context = primary_session.context
        merged_context.activeEntities.extend(secondary_session.context.activeEntities)

    return merged_context


def _get_default_channel_preference(agent: Agent, context: Optional[str]) -> ChannelType:
    """Get default channel preference based on agent type and context."""
    # Business logic for default preferences
    if context == "urgent":
        return ChannelType.VOICE
    elif context == "complex_query":
        return ChannelType.CHAT
    elif agent.type.value == "terminal":
        return ChannelType.VOICE  # Terminal agents prefer voice for quick updates
    else:
        return ChannelType.CHAT  # Default to chat for most scenarios