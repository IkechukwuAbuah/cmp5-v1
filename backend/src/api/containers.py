"""Container API endpoints."""

import time
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status, Query
from src.middleware.auth import get_current_agent
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address

from src.core.config import settings
from src.models.agent import Agent
from src.models.container import Container, ContainerResponse
from src.schemas.error import ErrorResponse
from src.localisation.cultural_messages import ErrorContext
from src.lib.error_utils import build_error_detail

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)




@router.get("/containers/{containerId}", response_model=Container)
# @limiter.limit("60/minute")  # Temporarily disabled for debugging
async def get_container(
    request: Request,
    containerId: str,
    agent: Agent = Depends(get_current_agent)
):
    """Get container details by ID."""
    try:
        # Validate agent permissions
        if not agent.can_access_container(containerId):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=build_error_detail(
                    "PERMISSION_DENIED",
                    ErrorContext.PERMISSION_DENIED,
                    container_id=containerId,
                    agent_id=agent.id,
                ),
            )

        # Query container data (mock implementation)
        container = await _get_container_from_external_apis(containerId, agent)

        if not container:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=build_error_detail(
                    "CONTAINER_NOT_FOUND",
                    ErrorContext.CONTAINER_NOT_FOUND,
                    container_id=containerId,
                ),
            )

        return container

    except HTTPException:
        raise
    except Exception as e:
        # Log error and return appropriate error response
        print(f"Get container error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=build_error_detail(
                "SYSTEM_UNAVAILABLE",
                ErrorContext.SYSTEM_UNAVAILABLE,
                operation="get_container",
                container_id=containerId,
            ),
        )


@router.get("/containers/{containerId}/milestones", response_model=dict)
# @limiter.limit("60/minute")  # Temporarily disabled for debugging
async def get_container_milestones(
    request: Request,
    containerId: str,
    limit: int = Query(20, ge=1, le=100, description="Maximum number of milestones to return"),
    offset: int = Query(0, ge=0, description="Number of milestones to skip"),
    agent: Agent = Depends(get_current_agent)
):
    """Get container milestone history with pagination."""
    try:
        # Validate agent permissions
        if not agent.can_access_container(containerId):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=build_error_detail(
                    "PERMISSION_DENIED",
                    ErrorContext.PERMISSION_DENIED,
                    container_id=containerId,
                    agent_id=agent.id,
                ),
            )

        # Query milestone data (mock implementation)
        milestones, total = await _get_container_milestones(containerId, limit, offset)

        return {
            "milestones": milestones,
            "total": total,
            "limit": limit,
            "offset": offset
        }

    except HTTPException:
        raise
    except Exception as e:
        # Log error and return appropriate error response
        print(f"Get container milestones error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=build_error_detail(
                "SYSTEM_UNAVAILABLE",
                ErrorContext.SYSTEM_UNAVAILABLE,
                operation="get_container_milestones",
                container_id=containerId,
            ),
        )


async def _get_container_from_external_apis(container_id: str, agent: Agent) -> Optional[Container]:
    """Get container data from external APIs."""
    # This would typically:
    # 1. Query EFL Terminal API first
    # 2. Fallback to CMA CGM API
    # 3. Apply circuit breaker protection
    # 4. Handle graceful degradation

    # Mock implementation
    return Container(
        id=container_id,
        containerNumber=container_id,
        isoCode="AB12",
        status="at_terminal",
        location={
            "id": "loc_1",
            "name": "Yard A1",
            "type": "yard",
            "coordinates": {"latitude": 6.4474, "longitude": 3.3903},
            "terminalId": "efl_terminal",
            "isActive": True
        },
        billOfLading={
            "id": "BL123",
            "blNumber": "ABC1234567",
            "vesselVoyage": {
                "id": "voy_1",
                "vesselName": "Marco Polo",
                "voyageNumber": "12345",
                "carrier": "CMA CGM",
                "originPort": "Lagos Port",
                "destinationPort": "EFL Terminal, Ikorodu",
                "estimatedDeparture": "2025-01-15T08:00:00Z",
                "estimatedArrival": "2025-01-15T14:00:00Z",
                "status": "in_transit"
            },
            "origin": "Lagos",
            "destination": "Ikorodu",
            "estimatedArrival": "2025-01-15T14:00:00Z",
            "shippingLine": "CMA CGM",
            "agentId": agent.id
        },
        agentId=agent.id,
        milestones=[],
        lastUpdated=time.time(),
        nextStep="Awaiting customs examination booking"
    )


async def _get_container_milestones(container_id: str, limit: int, offset: int) -> tuple[List, int]:
    """Get container milestones with pagination."""
    # Mock milestone data
    milestones = [
        {
            "id": f"mil_{i}",
            "containerId": container_id,
            "eventType": "discharged",
            "location": {
                "id": "loc_1",
                "name": "Yard A1",
                "type": "yard",
                "coordinates": {"latitude": 6.4474, "longitude": 3.3903},
                "terminalId": "efl_terminal",
                "isActive": True
            },
            "timestamp": f"2025-01-15T{10+i:02d}:00:00Z",
            "description": f"Mock milestone {i}",
            "source": "efl_terminal",
            "metadata": {}
        }
        for i in range(min(5, limit))  # Mock 5 milestones
    ]

    return milestones[offset:offset+limit], len(milestones)
