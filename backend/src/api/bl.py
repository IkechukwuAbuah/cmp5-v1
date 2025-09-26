"""Bill of Lading API endpoints."""

import time
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status
from src.middleware.auth import get_current_agent
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address

from src.core.config import settings
from src.models.agent import Agent
from src.models.container import BillOfLading, BillOfLadingResponse
from src.schemas.error import ErrorResponse

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)




@router.get("/bl/{blNumber}", response_model=BillOfLading)
@limiter.limit("60/minute")
async def get_bill_of_lading(
    request: Request,
    blNumber: str,
    agent: Agent = Depends(get_current_agent)
):
    """Get bill of lading details by BL number."""
    try:
        # Validate agent permissions
        if not agent.can_access_bl(blNumber):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions to access this bill of lading"
            )

        # Query BL data (mock implementation)
        bl = await _get_bl_from_external_apis(blNumber, agent)

        if not bl:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Bill of Lading with number {blNumber} not found"
            )

        return bl

    except HTTPException:
        raise
    except Exception as e:
        # Log error and return appropriate error response
        print(f"Get BL error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error while retrieving bill of lading"
        )


async def _get_bl_from_external_apis(bl_number: str, agent: Agent) -> Optional[BillOfLading]:
    """Get bill of lading data from external APIs."""
    # This would typically:
    # 1. Query CMA CGM API for BL data
    # 2. Fallback to EFL Terminal API if needed
    # 3. Apply circuit breaker protection
    # 4. Handle graceful degradation

    # Mock implementation
    return BillOfLading(
        id=bl_number,
        blNumber=bl_number,
        vesselVoyage={
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
        origin="Lagos",
        destination="Ikorodu",
        estimatedArrival="2025-01-15T14:00:00Z",
        shippingLine="CMA CGM",
        agentId=agent.id
    )
