"""Unit tests for TrackService logic (T064)."""

from datetime import datetime, timedelta
from typing import List
from unittest.mock import AsyncMock

import pytest

from src.models.agent import Agent, AgentType, ContactInfo, Permission
from src.models.bill_of_lading import BillOfLading
from src.models.container import Container, ContainerStatus
from src.models.terminal_location import LocationType, TerminalLocation
from src.models.vessel_voyage import VesselVoyage, VoyageStatus
from src.services.track_service import TrackService


def _make_permission(resource: str) -> Permission:
    """Helper to build permission instances."""
    return Permission(resource=resource, actions=["read"], conditions=None)


def _make_agent(allow_container: bool = True, allow_bl: bool = True) -> Agent:
    """Create a sample agent with configurable permissions."""
    permissions: List[Permission] = []
    if allow_container:
        permissions.append(_make_permission("container"))
    if allow_bl:
        permissions.append(_make_permission("bl"))

    return Agent(
        id="agent_123",
        name="Test Clearing Agent",
        type=AgentType.CLEARING,
        contactInfo=ContactInfo(
            phone="+2347012345678",
            email="agent@example.com",
            companyName="EFL Clearing"
        ),
        permissions=permissions,
    )


def _make_bill_of_lading(bl_number: str = "ABC1234567") -> BillOfLading:
    """Build a Bill of Lading object for testing."""
    eta = datetime.utcnow() + timedelta(days=2)
    etd = datetime.utcnow() - timedelta(days=10)
    return BillOfLading(
        id=bl_number,
        blNumber=bl_number,
        vesselVoyage=VesselVoyage(
            id="voy_001",
            vesselName="MV Test",
            voyageNumber="VOY123",
            carrier="CMA CGM",
            originPort="Lagos",
            destinationPort="Ikorodu",
            estimatedDeparture=etd,
            estimatedArrival=eta,
            status=VoyageStatus.IN_TRANSIT,
        ),
        origin="Lagos",
        destination="Ikorodu",
        estimatedArrival=eta,
        shippingLine="CMA CGM",
        agentId="agent_123",
    )


def _make_container(
    container_id: str = "EFLU1234567",
    status: ContainerStatus = ContainerStatus.AT_TERMINAL,
    next_step: str = "Awaiting customs examination",
) -> Container:
    """Build a Container object for testing."""
    return Container(
        id=container_id,
        containerNumber=container_id,
        isoCode="AB12",
        status=status,
        location=TerminalLocation(
            id="loc_001",
            name="Yard A",
            type=LocationType.YARD,
            coordinates=None,
            terminalId="efl_terminal",
            isActive=True,
        ),
        billOfLading=_make_bill_of_lading(),
        agentId="agent_123",
        milestones=[],
        lastUpdated=datetime.utcnow(),
        nextStep=next_step,
    )


@pytest.fixture
def track_service() -> TrackService:
    """Provide a fresh TrackService instance per test."""
    return TrackService()


class TestTrackContainer:
    """Tests for the track_container workflow."""

    @pytest.mark.asyncio
    async def test_requires_permission(self, track_service: TrackService, monkeypatch: pytest.MonkeyPatch) -> None:
        """Ensure tracking is denied when agent lacks container access."""
        agent = _make_agent(allow_container=False)
        efl_mock = AsyncMock(return_value=None)
        monkeypatch.setattr(track_service, "_get_container_from_efl_terminal", efl_mock)

        result = await track_service.track_container("EFLU1234567", agent)

        assert result is None
        assert efl_mock.await_count == 0

    @pytest.mark.asyncio
    async def test_returns_terminal_result_first(
        self,
        track_service: TrackService,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Verify the EFL Terminal lookup short-circuits the fallback chain."""
        agent = _make_agent()
        container = _make_container()

        efl_mock = AsyncMock(return_value=container)
        cma_mock = AsyncMock(return_value=None)
        cache_mock = AsyncMock(return_value=None)

        monkeypatch.setattr(track_service, "_get_container_from_efl_terminal", efl_mock)
        monkeypatch.setattr(track_service, "_get_container_from_cma_cgm", cma_mock)
        monkeypatch.setattr(track_service, "_get_container_from_cache", cache_mock)

        result = await track_service.track_container(container.id, agent)

        assert result is container
        assert efl_mock.await_count == 1
        assert cma_mock.await_count == 0
        assert cache_mock.await_count == 0

    @pytest.mark.asyncio
    async def test_falls_back_to_cache(
        self,
        track_service: TrackService,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Confirm fallback sequence reaches cache when upstream sources fail."""
        agent = _make_agent()
        container = _make_container(status=ContainerStatus.IN_TRANSIT)

        efl_mock = AsyncMock(return_value=None)
        cma_mock = AsyncMock(return_value=None)
        cache_mock = AsyncMock(return_value=container)

        monkeypatch.setattr(track_service, "_get_container_from_efl_terminal", efl_mock)
        monkeypatch.setattr(track_service, "_get_container_from_cma_cgm", cma_mock)
        monkeypatch.setattr(track_service, "_get_container_from_cache", cache_mock)

        result = await track_service.track_container(container.id, agent)

        assert result is container
        assert efl_mock.await_count == 1
        assert cma_mock.await_count == 1
        assert cache_mock.await_count == 1


class TestTrackBillOfLading:
    """Tests for the track_bl workflow."""

    @pytest.mark.asyncio
    async def test_requires_permission(self, track_service: TrackService, monkeypatch: pytest.MonkeyPatch) -> None:
        """Ensure BL tracking respects agent permissions."""
        agent = _make_agent(allow_bl=False)
        cma_mock = AsyncMock(return_value=None)
        monkeypatch.setattr(track_service, "_get_bl_from_cma_cgm", cma_mock)

        result = await track_service.track_bl("ABC1234567", agent)

        assert result is None
        assert cma_mock.await_count == 0

    @pytest.mark.asyncio
    async def test_returns_cma_before_terminal(
        self,
        track_service: TrackService,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Verify CMA CGM data is preferred before falling back to EFL Terminal."""
        agent = _make_agent()
        bill_of_lading = _make_bill_of_lading()

        cma_mock = AsyncMock(return_value=bill_of_lading)
        efl_mock = AsyncMock(return_value=None)

        monkeypatch.setattr(track_service, "_get_bl_from_cma_cgm", cma_mock)
        monkeypatch.setattr(track_service, "_get_bl_from_efl_terminal", efl_mock)

        result = await track_service.track_bl(bill_of_lading.blNumber, agent)

        assert result is bill_of_lading
        assert cma_mock.await_count == 1
        assert efl_mock.await_count == 0


class TestNaturalLanguageProcessing:
    """Tests for natural language query handling."""

    @pytest.mark.asyncio
    async def test_process_query_tracks_all_entities(
        self,
        track_service: TrackService,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Ensure containers and BLs extracted from text are tracked and returned."""
        agent = _make_agent()
        container = _make_container()
        bill_of_lading = _make_bill_of_lading()

        track_container_mock = AsyncMock(return_value=container)
        track_bl_mock = AsyncMock(return_value=bill_of_lading)

        monkeypatch.setattr(track_service, "track_container", track_container_mock)
        monkeypatch.setattr(track_service, "track_bl", track_bl_mock)

        query = "Please track container EFLU1234567 and BL ABC1234567 for me."
        result = await track_service.process_natural_language_query(query, agent)

        assert result["containers"] == [container]
        assert result["bill_of_ladings"] == [bill_of_lading]
        assert "EFLU1234567" in result["entities"]["containers"]
        assert "ABC1234567" in result["entities"]["bill_of_ladings"]
        track_container_mock.assert_awaited_once_with("EFLU1234567", agent)
        track_bl_mock.assert_awaited_once_with("ABC1234567", agent)


class TestDetermineNextStep:
    """Tests for next step guidance logic."""

    def test_handles_empty_container_list(self, track_service: TrackService) -> None:
        """Empty input should guide the user to provide identifiers."""
        result = track_service.determine_next_step([])
        assert "provide a valid container" in result.lower()

    def test_known_status_messages(self, track_service: TrackService) -> None:
        """Specific statuses should map to contextual guidance."""
        terminal_container = _make_container(status=ContainerStatus.AT_TERMINAL)
        cleared_container = _make_container(status=ContainerStatus.CLEARED_FOR_EXAM)
        released_container = _make_container(status=ContainerStatus.RELEASED)

        assert track_service.determine_next_step([terminal_container]) == "You may now book a customs examination."
        assert track_service.determine_next_step([cleared_container]) == "Customs examination has been scheduled. Please wait for inspection."
        assert track_service.determine_next_step([released_container]) == "Container is ready for pickup."

    def test_in_transit_message_includes_eta(self, track_service: TrackService) -> None:
        """In-transit containers should surface expected arrival details."""
        in_transit_container = _make_container(status=ContainerStatus.IN_TRANSIT)

        result = track_service.determine_next_step([in_transit_container])

        assert "in transit" in result.lower()
        assert str(in_transit_container.billOfLading.estimatedArrival) in result

    def test_unknown_status_falls_back_to_status_name(self, track_service: TrackService) -> None:
        """Statuses without explicit handling should produce a generic advisory."""
        delivered_container = _make_container(status=ContainerStatus.DELIVERED)

        result = track_service.determine_next_step([delivered_container])

        assert "current status" in result.lower()
        assert "delivered" in result.lower()
