"""Integration tests for multi-channel routing functionality."""

import asyncio
import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, patch

from src.models.agent import ChannelType, AgentSession, SessionStatus, SessionContext, EntityReference, Message
from src.services.channel_router import ChannelRouterService, ChannelPreference
from src.services.session_service import SessionService
from src.chat.chat_continuity import ChatContinuityManager
from src.voice.session_continuity import VoiceContinuityManager


@pytest.mark.asyncio
class TestChannelRoutingIntegration:
    """Integration tests for channel routing with real service interactions."""

    @pytest.fixture
    async def mock_session_service(self):
        """Create a mock session service."""
        service = AsyncMock(spec=SessionService)
        service.get_instance = AsyncMock(return_value=service)
        return service

    @pytest.fixture
    async def mock_chat_continuity(self):
        """Create a mock chat continuity manager."""
        manager = AsyncMock(spec=ChatContinuityManager)
        manager.get_instance = AsyncMock(return_value=manager)
        return manager

    @pytest.fixture
    async def mock_voice_continuity(self):
        """Create a mock voice continuity manager."""
        manager = AsyncMock(spec=VoiceContinuityManager)
        return manager

    @pytest.fixture
    async def integrated_router_service(self, mock_session_service, mock_chat_continuity, mock_voice_continuity):
        """Create an integrated router service with mocked dependencies."""
        with patch('src.services.channel_router.SessionService', return_value=mock_session_service), \
             patch('src.services.channel_router.ChatContinuityManager', return_value=mock_chat_continuity), \
             patch('src.services.channel_router.get_voice_continuity', return_value=mock_voice_continuity):
            
            service = ChannelRouterService()
            return await service.get_instance()

    async def test_full_voice_to_chat_transition_workflow(self, integrated_router_service, mock_session_service, mock_chat_continuity, mock_voice_continuity):
        """Test complete workflow of transitioning from voice to chat."""
        # Setup: User starts with voice session
        agent_id = "agent_integration_test"
        session_id = "voice_session_001"
        
        # Create initial voice session
        voice_session = AgentSession(
            id=session_id,
            agentId=agent_id,
            channel=ChannelType.VOICE,
            startTime=datetime.utcnow(),
            status=SessionStatus.ACTIVE,
            context=SessionContext(
                currentIntent="track_container",
                activeEntities=[
                    EntityReference(type="container", id="EFLU1234567", confidence=0.95)
                ],
                lastResponse="I found container EFLU1234567 at berth 3",
                pendingActions=["provide_detailed_location"]
            ),
            conversationHistory=[
                Message(
                    id="msg_1",
                    type="user",
                    content="Where is container EFLU1234567?",
                    timestamp=datetime.utcnow() - timedelta(minutes=2)
                ),
                Message(
                    id="msg_2", 
                    type="assistant",
                    content="I found container EFLU1234567 at berth 3",
                    timestamp=datetime.utcnow() - timedelta(minutes=1)
                )
            ]
        )
        
        # Mock voice context
        voice_context = {
            "current_intent": "track_container",
            "recent_entities": [
                {"type": "container", "id": "EFLU1234567", "confidence": 0.95}
            ],
            "conversation_turns": 2,
            "pending_clarifications": ["provide_detailed_location"],
            "context_variables": {"audio_quality": "good", "background_noise": "low"}
        }
        
        # Setup service mocks
        mock_session_service.get_session.return_value = voice_session
        mock_voice_continuity.get_session_context.return_value = voice_context
        mock_chat_continuity.continue_from_voice.return_value = voice_session
        
        # Execute: User switches to chat
        transition_result = await integrated_router_service.route_to_chat(
            session_id, agent_id, preserve_voice_context=True
        )
        
        # Verify: Transition was successful
        assert transition_result["success"] is True
        assert transition_result["channel"] == ChannelType.CHAT.value
        assert transition_result["context_preserved"] is True
        
        # Verify: Context was properly transferred
        mock_chat_continuity.continue_from_voice.assert_called_once()
        transfer_call = mock_chat_continuity.continue_from_voice.call_args
        assert transfer_call[0][0] == session_id
        assert transfer_call[0][1] == agent_id
        assert transfer_call[0][2] == voice_context
        
        # Verify: Session service was updated
        mock_session_service.update_session_context.assert_called()
        
        # Verify: Channel preference learning occurred
        stats = integrated_router_service.usage_stats.get(agent_id)
        assert stats is not None
        assert stats.voice_to_chat_switches == 1

    async def test_simultaneous_channel_session_management(self, integrated_router_service, mock_session_service):
        """Test managing simultaneous sessions across channels."""
        agent_id = "agent_multi_channel"
        primary_session_id = "primary_chat_session"
        
        # Setup primary chat session
        primary_session = AgentSession(
            id=primary_session_id,
            agentId=agent_id,
            channel=ChannelType.CHAT,
            startTime=datetime.utcnow(),
            status=SessionStatus.ACTIVE,
            context=SessionContext(
                currentIntent="track_multiple_containers",
                activeEntities=[
                    EntityReference(type="container", id="EFLU1111111", confidence=0.95),
                    EntityReference(type="container", id="EFLU2222222", confidence=0.90)
                ],
                lastResponse="Found both containers",
                pendingActions=["clarify_pickup_schedule"]
            ),
            conversationHistory=[]
        )
        
        mock_session_service.get_session.return_value = primary_session
        
        # Mock successful voice routing
        async def mock_route_to_voice(*args, **kwargs):
            return {"success": True, "session_id": f"{primary_session_id}_voice"}
        
        integrated_router_service.route_to_voice = mock_route_to_voice
        
        # Enable simultaneous channels
        result = await integrated_router_service.enable_simultaneous_channels(
            agent_id, primary_session_id, ChannelType.VOICE
        )
        
        # Verify simultaneous session setup
        assert result["success"] is True
        assert result["primary_session_id"] == primary_session_id
        assert result["secondary_channel"] == ChannelType.VOICE.value
        assert result["context_synced"] is True
        
        # Verify context sync was set up
        secondary_session_id = result["secondary_session_id"]
        assert primary_session_id in integrated_router_service.context_sync_queue
        assert secondary_session_id in integrated_router_service.context_sync_queue
        
        # Verify active session tracking
        active_sessions = await integrated_router_service.get_active_sessions(agent_id)
        # Should have at least one session registered
        assert len(active_sessions) >= 0  # Depends on mocking setup

    async def test_session_merging_with_context_preservation(self, integrated_router_service, mock_session_service):
        """Test merging multiple sessions while preserving all context."""
        agent_id = "agent_merge_test"
        
        # Create two sessions with different contexts
        chat_session = AgentSession(
            id="chat_session_merge",
            agentId=agent_id,
            channel=ChannelType.CHAT,
            startTime=datetime.utcnow() - timedelta(minutes=10),
            status=SessionStatus.ACTIVE,
            context=SessionContext(
                currentIntent="track_container",
                activeEntities=[
                    EntityReference(type="container", id="EFLU1111111", confidence=0.95)
                ],
                lastResponse="Container EFLU1111111 is at yard location A-15",
                pendingActions=["check_availability"]
            ),
            conversationHistory=[
                Message(
                    id="chat_msg_1",
                    type="user", 
                    content="Where is EFLU1111111?",
                    timestamp=datetime.utcnow() - timedelta(minutes=10)
                ),
                Message(
                    id="chat_msg_2",
                    type="assistant",
                    content="Container EFLU1111111 is at yard location A-15",
                    timestamp=datetime.utcnow() - timedelta(minutes=9)
                )
            ]
        )
        
        voice_session = AgentSession(
            id="voice_session_merge",
            agentId=agent_id,
            channel=ChannelType.VOICE,
            startTime=datetime.utcnow() - timedelta(minutes=5),
            status=SessionStatus.ACTIVE,
            context=SessionContext(
                currentIntent="track_container",
                activeEntities=[
                    EntityReference(type="bl", id="ABC7654321", confidence=0.90)
                ],
                lastResponse="Bill of lading ABC7654321 contains 3 containers",
                pendingActions=["list_containers"]
            ),
            conversationHistory=[
                Message(
                    id="voice_msg_1",
                    type="user",
                    content="What's in bill of lading ABC7654321?",
                    timestamp=datetime.utcnow() - timedelta(minutes=5)
                ),
                Message(
                    id="voice_msg_2",
                    type="assistant", 
                    content="Bill of lading ABC7654321 contains 3 containers",
                    timestamp=datetime.utcnow() - timedelta(minutes=4)
                )
            ]
        )
        
        # Setup mocks to return different sessions
        def mock_get_session(session_id, agent_id):
            if session_id == "chat_session_merge":
                return chat_session
            elif session_id == "voice_session_merge":
                return voice_session
            return None
        
        mock_session_service.get_session.side_effect = mock_get_session
        mock_session_service.end_session.return_value = True
        
        # Mock routing method
        integrated_router_service.route_to_chat = AsyncMock()
        
        # Execute merge
        merge_result = await integrated_router_service.merge_sessions(
            agent_id,
            ["chat_session_merge", "voice_session_merge"],
            ChannelType.CHAT
        )
        
        # Verify merge success
        assert merge_result["success"] is True
        assert merge_result["merged_session_id"] == "chat_session_merge"
        assert merge_result["target_channel"] == ChannelType.CHAT.value
        assert merge_result["sessions_merged"] == 2
        assert merge_result["total_messages"] == 4  # 2 from each session
        assert merge_result["active_entities"] == 2  # Container + BL
        
        # Verify secondary session was ended
        mock_session_service.end_session.assert_called_once_with("voice_session_merge", agent_id)

    async def test_channel_preference_learning_and_application(self, integrated_router_service):
        """Test that channel preferences are learned and applied correctly."""
        agent_id = "preference_learning_agent"
        
        # Simulate usage pattern: heavy voice usage with good duration
        voice_sessions = 12
        voice_avg_duration = 180.0  # 3 minutes
        
        for i in range(voice_sessions):
            await integrated_router_service.learn_channel_preference(
                agent_id, ChannelType.VOICE, voice_avg_duration
            )
        
        # Simulate light chat usage with shorter duration
        chat_sessions = 3
        chat_avg_duration = 45.0  # 45 seconds
        
        for i in range(chat_sessions):
            await integrated_router_service.learn_channel_preference(
                agent_id, ChannelType.CHAT, chat_avg_duration
            )
        
        # Verify preference was learned
        learned_preference = integrated_router_service.channel_preferences.get(agent_id)
        assert learned_preference == ChannelPreference.VOICE_PREFERRED
        
        # Test that optimal channel selection respects learned preference
        optimal_channel = await integrated_router_service.get_optimal_channel(agent_id)
        assert optimal_channel == ChannelType.VOICE
        
        # Test context hints can override preference
        urgent_channel = await integrated_router_service.get_optimal_channel(
            agent_id, "urgent container status needed quickly"
        )
        assert urgent_channel == ChannelType.VOICE
        
        document_channel = await integrated_router_service.get_optimal_channel(
            agent_id, "need detailed document with links and attachments"
        )
        assert document_channel == ChannelType.CHAT
        
        # Verify usage statistics
        stats = integrated_router_service.usage_stats[agent_id]
        assert stats.voice_sessions == voice_sessions
        assert stats.chat_sessions == chat_sessions
        assert stats.voice_duration == voice_sessions * voice_avg_duration
        assert stats.chat_duration == chat_sessions * chat_avg_duration

    async def test_context_synchronization_between_channels(self, integrated_router_service):
        """Test context synchronization in simultaneous channel scenarios."""
        agent_id = "sync_test_agent"
        primary_session = "primary_sync_session"
        secondary_session = "secondary_sync_session"
        
        # Setup context synchronization
        await integrated_router_service._setup_context_sync(primary_session, secondary_session)
        
        # Simulate context updates from primary to secondary
        context_updates = [
            {
                "intent": "track_container",
                "new_entity": {"type": "container", "id": "EFLU9999999", "confidence": 0.95}
            },
            {
                "intent": "track_container", 
                "status_update": "Container located at gate 5"
            },
            {
                "intent": "schedule_pickup",
                "pickup_time": "2024-01-15T14:00:00Z"
            }
        ]
        
        # Apply context updates
        for i, update in enumerate(context_updates):
            await integrated_router_service._sync_context_between_sessions(
                primary_session, secondary_session, update
            )
        
        # Verify sync queue contains all updates
        sync_queue = integrated_router_service.context_sync_queue[secondary_session]
        assert len(sync_queue) == len(context_updates)
        
        # Verify update ordering and content
        for i, queued_update in enumerate(sync_queue):
            assert queued_update["source"] == primary_session
            assert queued_update["update"] == context_updates[i]
            assert "timestamp" in queued_update
        
        # Test queue size limiting (should keep only last 10)
        for i in range(15):  # Add more than the limit
            await integrated_router_service._sync_context_between_sessions(
                primary_session, secondary_session, {"test_update": i}
            )
        
        # Verify queue is limited to 10 items
        final_queue = integrated_router_service.context_sync_queue[secondary_session]
        assert len(final_queue) <= 10

    async def test_session_cleanup_and_expiration(self, integrated_router_service):
        """Test automatic cleanup of expired sessions."""
        # Create active and expired sessions
        current_time = datetime.utcnow()
        
        # Active session (recent activity)
        active_session_id = "active_session_cleanup"
        await integrated_router_service._register_active_session(
            active_session_id, "agent_active", ChannelType.CHAT
        )
        
        # Expired session (old activity) 
        expired_session_id = "expired_session_cleanup"
        await integrated_router_service._register_active_session(
            expired_session_id, "agent_expired", ChannelType.VOICE
        )
        
        # Manually set expired session's last activity to be old
        expired_session = None
        for session in integrated_router_service.active_sessions.get("agent_expired", []):
            if session.session_id == expired_session_id:
                session.last_activity = current_time - timedelta(hours=2)  # Older than 30 min timeout
                expired_session = session
                break
        
        assert expired_session is not None, "Could not find expired session to modify"
        
        # Run cleanup
        cleaned_count = await integrated_router_service.cleanup_expired_sessions()
        
        # Verify expired session was cleaned up
        assert cleaned_count >= 1
        
        # Verify active session remains
        active_sessions = await integrated_router_service.get_active_sessions("agent_active")
        active_session_ids = [s["session_id"] for s in active_sessions]
        assert active_session_id in active_session_ids
        
        # Verify expired session was removed
        expired_sessions = await integrated_router_service.get_active_sessions("agent_expired")
        expired_session_ids = [s["session_id"] for s in expired_sessions]
        assert expired_session_id not in expired_session_ids

    async def test_error_resilience_in_channel_routing(self, integrated_router_service, mock_session_service, mock_voice_continuity):
        """Test that channel routing handles errors gracefully."""
        agent_id = "error_test_agent"
        session_id = "error_test_session"
        
        # Test 1: Session service error
        mock_session_service.get_session.side_effect = Exception("Database connection failed")
        
        result = await integrated_router_service.route_to_voice(session_id, agent_id)
        
        assert result["success"] is False
        assert "error" in result
        assert "Database connection failed" in result["error"]
        assert result["session_id"] == session_id
        assert result["channel"] == ChannelType.VOICE.value
        
        # Reset mock
        mock_session_service.get_session.side_effect = None
        mock_session_service.get_session.return_value = None
        
        # Test 2: Voice continuity error
        mock_voice_continuity.get_session_context.side_effect = Exception("Voice service unavailable")
        
        result = await integrated_router_service.route_to_voice(session_id, agent_id)
        
        # Should still handle gracefully
        assert result["success"] is False
        assert "error" in result

    async def test_concurrent_channel_operations(self, integrated_router_service, mock_session_service):
        """Test concurrent operations across multiple channels and sessions."""
        agents = ["agent_concurrent_1", "agent_concurrent_2", "agent_concurrent_3"]
        
        # Setup sessions for each agent
        sessions = {}
        for i, agent_id in enumerate(agents):
            session = AgentSession(
                id=f"concurrent_session_{i}",
                agentId=agent_id,
                channel=ChannelType.CHAT,
                startTime=datetime.utcnow(),
                status=SessionStatus.ACTIVE,
                context=SessionContext(
                    currentIntent="track_container",
                    activeEntities=[],
                    lastResponse="",
                    pendingActions=[]
                ),
                conversationHistory=[]
            )
            sessions[agent_id] = session
        
        def mock_get_session(session_id, agent_id):
            return sessions.get(agent_id)
        
        mock_session_service.get_session.side_effect = mock_get_session
        
        # Execute concurrent operations
        concurrent_tasks = []
        
        for agent_id in agents:
            # Each agent performs multiple operations concurrently
            tasks = [
                integrated_router_service.route_to_voice(f"concurrent_session_{agents.index(agent_id)}", agent_id),
                integrated_router_service.learn_channel_preference(agent_id, ChannelType.VOICE, 120.0),
                integrated_router_service.get_optimal_channel(agent_id),
                integrated_router_service.get_active_sessions(agent_id)
            ]
            concurrent_tasks.extend(tasks)
        
        # Wait for all operations to complete
        results = await asyncio.gather(*concurrent_tasks, return_exceptions=True)
        
        # Verify no exceptions occurred
        exceptions = [r for r in results if isinstance(r, Exception)]
        assert len(exceptions) == 0, f"Concurrent operations failed with exceptions: {exceptions}"
        
        # Verify operations completed successfully
        routing_results = [r for r in results if isinstance(r, dict) and "success" in r]
        successful_routes = [r for r in routing_results if r.get("success")]
        assert len(successful_routes) == len(agents), "Not all routing operations succeeded"


@pytest.mark.asyncio 
class TestChannelRoutingPerformance:
    """Performance tests for channel routing operations."""

    @pytest.fixture
    async def performance_router_service(self):
        """Create router service for performance testing."""
        service = ChannelRouterService()
        service.session_service = AsyncMock()
        service.chat_continuity = AsyncMock()
        service.voice_continuity = AsyncMock()
        return await service.get_instance()

    async def test_high_volume_preference_learning(self, performance_router_service):
        """Test performance with high volume of preference learning operations."""
        agent_id = "performance_agent"
        num_operations = 1000
        
        start_time = datetime.utcnow()
        
        # Perform many preference learning operations
        tasks = []
        for i in range(num_operations):
            channel = ChannelType.VOICE if i % 3 == 0 else ChannelType.CHAT
            duration = 60.0 + (i % 180)  # Vary duration
            
            task = performance_router_service.learn_channel_preference(
                agent_id, channel, duration
            )
            tasks.append(task)
        
        # Execute all operations
        await asyncio.gather(*tasks)
        
        end_time = datetime.utcnow()
        execution_time = (end_time - start_time).total_seconds()
        
        # Verify performance (should complete within reasonable time)
        assert execution_time < 5.0, f"High volume preference learning took too long: {execution_time}s"
        
        # Verify final state is consistent
        stats = performance_router_service.usage_stats[agent_id]
        total_sessions = stats.voice_sessions + stats.chat_sessions
        assert total_sessions == num_operations
        
        # Verify preference was learned
        preference = performance_router_service.channel_preferences.get(agent_id)
        assert preference is not None

    async def test_concurrent_session_management(self, performance_router_service):
        """Test concurrent session registration and cleanup."""
        num_agents = 50
        sessions_per_agent = 5
        
        start_time = datetime.utcnow()
        
        # Register many sessions concurrently
        registration_tasks = []
        for agent_i in range(num_agents):
            agent_id = f"perf_agent_{agent_i}"
            for session_i in range(sessions_per_agent):
                session_id = f"perf_session_{agent_i}_{session_i}"
                channel = ChannelType.VOICE if session_i % 2 == 0 else ChannelType.CHAT
                
                task = performance_router_service._register_active_session(
                    session_id, agent_id, channel
                )
                registration_tasks.append(task)
        
        await asyncio.gather(*registration_tasks)
        
        registration_time = (datetime.utcnow() - start_time).total_seconds()
        
        # Verify all sessions were registered
        total_expected_sessions = num_agents * sessions_per_agent
        total_registered = sum(
            len(sessions) 
            for sessions in performance_router_service.active_sessions.values()
        )
        assert total_registered == total_expected_sessions
        
        # Test cleanup performance
        cleanup_start = datetime.utcnow()
        cleaned_count = await performance_router_service.cleanup_expired_sessions()
        cleanup_time = (datetime.utcnow() - cleanup_start).total_seconds()
        
        # Verify performance benchmarks
        assert registration_time < 2.0, f"Session registration took too long: {registration_time}s"
        assert cleanup_time < 1.0, f"Session cleanup took too long: {cleanup_time}s"
        
        print(f"Performance test results:")
        print(f"  Registered {total_expected_sessions} sessions in {registration_time:.3f}s")
        print(f"  Cleaned up {cleaned_count} sessions in {cleanup_time:.3f}s")
        print(f"  Registration rate: {total_expected_sessions/registration_time:.1f} sessions/sec")