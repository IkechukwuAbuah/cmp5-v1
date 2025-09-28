"""Unit tests for ChannelRouterService multi-channel routing (T052.4)."""

from datetime import datetime
from typing import Dict
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.models.agent import ChannelType
from src.models.agent_session import AgentSession, SessionStatus
from src.models.session_context import EntityReference, SessionContext
from src.services.channel_router import ChannelRouterService


def _build_session_context() -> SessionContext:
    """Create a session context populated with chat data."""
    return SessionContext(
        currentIntent="track_container",
        activeEntities=[
            EntityReference(type="container", id="EFLU1234567", confidence=0.92)
        ],
        preferredChannel=ChannelType.CHAT,
        lastResponse="Container EFLU1234567 is awaiting customs exam",
        pendingActions=["confirm_eta"],
    )


def _build_session() -> AgentSession:
    """Create an agent session using the sample context."""
    return AgentSession(
        id="sess-123",
        agentId="agent-789",
        channel=ChannelType.CHAT,
        startTime=datetime.utcnow(),
        status=SessionStatus.ACTIVE,
        context=_build_session_context(),
        conversationHistory=[],
    )


@pytest.mark.asyncio
async def test_route_to_voice_transfers_chat_context():
    """Routing to voice should hydrate voice context and mark preference."""
    session = _build_session()

    router = ChannelRouterService()
    router.session_service = AsyncMock()
    router.session_service.get_session = AsyncMock(return_value=session)
    router.session_service.create_session = AsyncMock()
    router.session_service.update_session_context = AsyncMock(return_value=True)

    voice_state = MagicMock()
    voice_state.session_id = session.id
    voice_state.get_relevant_context.return_value = {
        "current_intent": session.context.currentIntent,
        "recent_entities": session.context.activeEntities,
        "pending_clarifications": session.context.pendingActions,
        "context_variables": {"last_chat_response": session.context.lastResponse},
        "conversation_turns": 2,
    }

    voice_manager = AsyncMock()
    voice_manager.sync_from_chat = AsyncMock(return_value=voice_state)

    with patch("src.services.channel_router.get_voice_continuity", new=AsyncMock(return_value=voice_manager)) as mock_get_voice:
        result = await router.route_to_voice(session.id, session.agentId, {"phone_number": "+2347012345678"})

    mock_get_voice.assert_awaited_once()
    voice_manager.sync_from_chat.assert_awaited_once()

    assert result["channel"] == ChannelType.VOICE.value
    assert result["sessionId"] == session.id
    assert result["context"]["preferredChannel"] == ChannelType.VOICE.value
    assert result["context"]["recent_entities"][0]["id"] == "EFLU1234567"
    assert session.context.preferredChannel == ChannelType.VOICE
    router.session_service.update_session_context.assert_awaited_with(session.id, session.context)


@pytest.mark.asyncio
async def test_route_to_chat_merges_voice_context():
    """Routing to chat should merge in voice context and update preference."""
    session = _build_session()
    session.context.pendingActions = ["book_exam"]
    session.context.preferredChannel = ChannelType.VOICE
    session.channel = ChannelType.VOICE

    router = ChannelRouterService()
    router.session_service = AsyncMock()
    router.session_service.get_session = AsyncMock(return_value=session)
    router.session_service.create_session = AsyncMock()
    router.session_service.update_session_context = AsyncMock(return_value=True)

    async def _continue_from_voice(session_id: str, agent_id: str, voice_ctx: Dict):
        session.context.currentIntent = voice_ctx.get("current_intent")
        entities = [
            EntityReference(**item)
            for item in voice_ctx.get("recent_entities", [])
        ]
        session.context.activeEntities = entities
        session.context.pendingActions.extend(voice_ctx.get("pending_clarifications", []))
        session.context.preferredChannel = ChannelType.CHAT
        return session

    router.chat_continuity = AsyncMock()
    router.chat_continuity.continue_from_voice = AsyncMock(side_effect=_continue_from_voice)

    voice_context = {
        "current_intent": "track_container",
        "recent_entities": [
            {"type": "container", "id": "EFLU9999999", "confidence": 0.9}
        ],
        "pending_clarifications": ["confirm_eta"],
    }

    result = await router.route_to_chat(session.id, session.agentId, voice_context)

    router.chat_continuity.continue_from_voice.assert_awaited_once()
    router.session_service.update_session_context.assert_awaited_with(session.id, session.context)

    assert result["channel"] == ChannelType.CHAT.value
    assert result["context"]["preferredChannel"] == ChannelType.CHAT.value
    assert result["context"]["pendingActions"] == ["book_exam", "confirm_eta"]
    assert result["context"]["activeEntities"][0]["id"] == "EFLU9999999"
    assert session.context.preferredChannel == ChannelType.CHAT
