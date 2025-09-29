"""Integration tests for channel routing API endpoints."""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch

from src.main import app
from src.models.agent import Agent, AgentType, ContactInfo, ChannelType


class TestChannelRoutingAPI:
    """Integration tests for channel routing API endpoints."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)

    @pytest.fixture
    def mock_agent(self):
        """Create mock agent for testing."""
        return Agent(
            id="test_agent_123",
            name="Test Clearing Agency",
            type=AgentType.CLEARING,
            contactInfo=ContactInfo(
                phone="+234-123-4567",
                email="test@example.com",
                companyName="Test Company"
            )
        )

    @pytest.fixture
    def auth_headers(self):
        """Create authentication headers for testing."""
        return {"Authorization": "Bearer test_token"}

    @patch('src.middleware.auth.get_current_agent')
    @patch('src.services.channel_router.ChannelRouterService.get_instance')
    @patch('src.services.session_service.SessionService.get_instance')
    async def test_switch_channel_success(self, mock_session_service, mock_router_service, mock_get_agent, client, mock_agent, auth_headers):
        """Test successful channel switching."""
        # Setup mocks
        mock_get_agent.return_value = mock_agent
        
        mock_session = AsyncMock()
        mock_session.id = "test_session_123"
        mock_session.channel = ChannelType.CHAT
        mock_session.context = AsyncMock()
        
        mock_session_service_instance = AsyncMock()
        mock_session_service_instance.get_session.return_value = mock_session
        mock_session_service.return_value = mock_session_service_instance
        
        mock_router_instance = AsyncMock()
        mock_router_instance.route_to_voice.return_value = {
            "current_intent": "track_container",
            "recent_entities": []
        }
        mock_router_service.return_value = mock_router_instance

        # Test request
        response = client.post(
            "/api/v1/channel-routing/switch",
            json={
                "session_id": "test_session_123",
                "target_channel": "voice",
                "preserve_history": True
            },
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["session_id"] == "test_session_123"
        assert data["channel"] == "voice"

    @patch('src.middleware.auth.get_current_agent')
    async def test_switch_channel_session_not_found(self, mock_get_agent, client, mock_agent, auth_headers):
        """Test channel switching with non-existent session."""
        mock_get_agent.return_value = mock_agent

        with patch('src.services.session_service.SessionService.get_instance') as mock_session_service:
            mock_session_service_instance = AsyncMock()
            mock_session_service_instance.get_session.return_value = None
            mock_session_service.return_value = mock_session_service_instance

            response = client.post(
                "/api/v1/channel-routing/switch",
                json={
                    "session_id": "nonexistent_session",
                    "target_channel": "voice"
                },
                headers=auth_headers
            )

            assert response.status_code == 404
            assert "Session not found" in response.json()["detail"]

    @patch('src.middleware.auth.get_current_agent')
    async def test_switch_channel_invalid_target(self, mock_get_agent, client, mock_agent, auth_headers):
        """Test channel switching with invalid target channel."""
        mock_get_agent.return_value = mock_agent

        response = client.post(
            "/api/v1/channel-routing/switch",
            json={
                "session_id": "test_session_123",
                "target_channel": "invalid_channel"
            },
            headers=auth_headers
        )

        assert response.status_code == 422  # Validation error

    @patch('src.middleware.auth.get_current_agent')
    @patch('src.services.session_service.SessionService.get_instance')
    async def test_merge_sessions_success(self, mock_session_service, mock_get_agent, client, mock_agent, auth_headers):
        """Test successful session merging."""
        mock_get_agent.return_value = mock_agent

        # Setup mock sessions
        primary_session = AsyncMock()
        primary_session.id = "primary_session"
        primary_session.channel = ChannelType.CHAT
        primary_session.context = AsyncMock()

        secondary_session = AsyncMock()
        secondary_session.id = "secondary_session"
        secondary_session.channel = ChannelType.VOICE
        secondary_session.context = AsyncMock()

        mock_session_service_instance = AsyncMock()
        mock_session_service_instance.get_session.side_effect = [primary_session, secondary_session]
        mock_session_service_instance.update_session_context.return_value = True
        mock_session_service_instance.end_session.return_value = True
        mock_session_service.return_value = mock_session_service_instance

        response = client.post(
            "/api/v1/channel-routing/merge-sessions",
            json={
                "primary_session_id": "primary_session",
                "secondary_session_id": "secondary_session",
                "merge_strategy": "preserve_primary"
            },
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["merged_session_id"] == "primary_session"

    @patch('src.middleware.auth.get_current_agent')
    async def test_merge_sessions_same_channel_error(self, mock_get_agent, client, mock_agent, auth_headers):
        """Test session merging error when both sessions are from same channel."""
        mock_get_agent.return_value = mock_agent

        with patch('src.services.session_service.SessionService.get_instance') as mock_session_service:
            # Both sessions from same channel
            session1 = AsyncMock()
            session1.channel = ChannelType.CHAT
            session2 = AsyncMock()
            session2.channel = ChannelType.CHAT

            mock_session_service_instance = AsyncMock()
            mock_session_service_instance.get_session.side_effect = [session1, session2]
            mock_session_service.return_value = mock_session_service_instance

            response = client.post(
                "/api/v1/channel-routing/merge-sessions",
                json={
                    "primary_session_id": "session1",
                    "secondary_session_id": "session2"
                },
                headers=auth_headers
            )

            assert response.status_code == 400
            assert "Cannot merge sessions from the same channel" in response.json()["detail"]

    @patch('src.middleware.auth.get_current_agent')
    async def test_set_channel_preference_success(self, mock_get_agent, client, mock_agent, auth_headers):
        """Test setting channel preference."""
        mock_get_agent.return_value = mock_agent

        response = client.post(
            "/api/v1/channel-routing/set-preference",
            json={
                "preferred_channel": "voice",
                "context": "urgent"
            },
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["agent_id"] == mock_agent.id
        assert data["preferred_channel"] == "voice"

    @patch('src.middleware.auth.get_current_agent')
    async def test_get_channel_preference_success(self, mock_get_agent, client, mock_agent, auth_headers):
        """Test getting channel preference."""
        mock_get_agent.return_value = mock_agent

        response = client.get(
            "/api/v1/channel-routing/preference",
            params={"context": "urgent"},
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert "agent_id" in data
        assert "preferred_channel" in data
        assert "confidence" in data

    @patch('src.middleware.auth.get_current_agent')
    async def test_get_session_channel_history_success(self, mock_get_agent, client, mock_agent, auth_headers):
        """Test getting session channel history."""
        mock_get_agent.return_value = mock_agent

        with patch('src.services.session_service.SessionService.get_instance') as mock_session_service:
            mock_session = AsyncMock()
            mock_session.channel = ChannelType.CHAT
            mock_session.startTime = AsyncMock()
            mock_session.endTime = None
            mock_session.conversationHistory = []

            mock_session_service_instance = AsyncMock()
            mock_session_service_instance.get_session.return_value = mock_session
            mock_session_service.return_value = mock_session_service_instance

            response = client.get(
                "/api/v1/channel-routing/session/test_session_123/channels",
                headers=auth_headers
            )

            assert response.status_code == 200
            data = response.json()
            assert data["session_id"] == "test_session_123"
            assert "current_channel" in data
            assert "channel_history" in data

    @patch('src.middleware.auth.get_current_agent')
    async def test_get_session_channel_history_not_found(self, mock_get_agent, client, mock_agent, auth_headers):
        """Test getting channel history for non-existent session."""
        mock_get_agent.return_value = mock_agent

        with patch('src.services.session_service.SessionService.get_instance') as mock_session_service:
            mock_session_service_instance = AsyncMock()
            mock_session_service_instance.get_session.return_value = None
            mock_session_service.return_value = mock_session_service_instance

            response = client.get(
                "/api/v1/channel-routing/session/nonexistent/channels",
                headers=auth_headers
            )

            assert response.status_code == 404

    @patch('src.middleware.auth.get_current_agent')
    async def test_get_channel_routing_stats_success(self, mock_get_agent, client, mock_agent, auth_headers):
        """Test getting channel routing statistics."""
        mock_get_agent.return_value = mock_agent

        response = client.get(
            "/api/v1/channel-routing/stats",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert "agent_id" in data
        assert "total_sessions" in data
        assert "channel_distribution" in data
        assert "switch_count" in data

    async def test_channel_routing_endpoints_require_auth(self, client):
        """Test that channel routing endpoints require authentication."""
        # Test switch endpoint
        response = client.post(
            "/api/v1/channel-routing/switch",
            json={"session_id": "test", "target_channel": "voice"}
        )
        assert response.status_code in [401, 403]

        # Test preference endpoint
        response = client.post(
            "/api/v1/channel-routing/set-preference",
            json={"preferred_channel": "voice"}
        )
        assert response.status_code in [401, 403]

        # Test stats endpoint
        response = client.get("/api/v1/channel-routing/stats")
        assert response.status_code in [401, 403]

    @patch('src.middleware.auth.get_current_agent')
    async def test_switch_channel_with_context_override(self, mock_get_agent, client, mock_agent, auth_headers):
        """Test channel switching with context override."""
        mock_get_agent.return_value = mock_agent

        with patch('src.services.session_service.SessionService.get_instance') as mock_session_service:
            with patch('src.services.channel_router.ChannelRouterService.get_instance') as mock_router_service:
                mock_session = AsyncMock()
                mock_session.channel = ChannelType.CHAT
                mock_session.context = AsyncMock()
                
                mock_session_service_instance = AsyncMock()
                mock_session_service_instance.get_session.return_value = mock_session
                mock_session_service.return_value = mock_session_service_instance
                
                mock_router_instance = AsyncMock()
                mock_router_instance.route_to_voice.return_value = {"context": "overridden"}
                mock_router_service.return_value = mock_router_instance

                response = client.post(
                    "/api/v1/channel-routing/switch",
                    json={
                        "session_id": "test_session_123",
                        "target_channel": "voice",
                        "context_override": {"custom_key": "custom_value"}
                    },
                    headers=auth_headers
                )

                assert response.status_code == 200
                # Verify context override was passed
                mock_router_instance.route_to_voice.assert_called_with(
                    session_id="test_session_123",
                    agent_id=mock_agent.id,
                    context_override={"custom_key": "custom_value"}
                )

    @patch('src.middleware.auth.get_current_agent')
    async def test_merge_sessions_different_strategies(self, mock_get_agent, client, mock_agent, auth_headers):
        """Test session merging with different strategies."""
        mock_get_agent.return_value = mock_agent

        with patch('src.services.session_service.SessionService.get_instance') as mock_session_service:
            primary_session = AsyncMock()
            primary_session.channel = ChannelType.CHAT
            secondary_session = AsyncMock()
            secondary_session.channel = ChannelType.VOICE

            mock_session_service_instance = AsyncMock()
            mock_session_service_instance.get_session.side_effect = [primary_session, secondary_session]
            mock_session_service_instance.update_session_context.return_value = True
            mock_session_service_instance.end_session.return_value = True
            mock_session_service.return_value = mock_session_service_instance

            # Test different merge strategies
            strategies = ["preserve_primary", "merge_context", "interleave"]
            
            for strategy in strategies:
                response = client.post(
                    "/api/v1/channel-routing/merge-sessions",
                    json={
                        "primary_session_id": "primary",
                        "secondary_session_id": "secondary",
                        "merge_strategy": strategy
                    },
                    headers=auth_headers
                )

                assert response.status_code == 200
                data = response.json()
                assert strategy in data["message"]