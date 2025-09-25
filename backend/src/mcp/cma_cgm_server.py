"""MCP server for CMA CGM API integration."""

import asyncio
from typing import Dict, List, Any, Optional

from src.core.config import settings
from src.services.external_api_service import ExternalAPIService


class CMACGMMCPServer:
    """MCP server for CMA CGM API integration."""

    def __init__(self):
        self.api_service = None
        self._tools = {}

    async def get_instance(self) -> "CMACGMMCPServer":
        """Get singleton instance with dependencies initialized."""
        if self.api_service is None:
            self.api_service = await ExternalAPIService().get_instance()
        return self

    def get_tools(self) -> List[Dict[str, Any]]:
        """Get list of available MCP tools."""
        return [
            {
                "name": "get_container_status",
                "description": "Get current status of a container from CMA CGM",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "container_id": {
                            "type": "string",
                            "description": "Container ID (e.g., EFLU7896543)"
                        }
                    },
                    "required": ["container_id"]
                }
            },
            {
                "name": "get_bl_status",
                "description": "Get bill of lading status and associated containers",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "bl_number": {
                            "type": "string",
                            "description": "Bill of Lading number (e.g., ABC1234567)"
                        }
                    },
                    "required": ["bl_number"]
                }
            },
            {
                "name": "search_shipments",
                "description": "Search shipments by various criteria",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "origin": {
                            "type": "string",
                            "description": "Origin port"
                        },
                        "destination": {
                            "type": "string",
                            "description": "Destination port"
                        },
                        "vessel": {
                            "type": "string",
                            "description": "Vessel name"
                        },
                        "voyage": {
                            "type": "string",
                            "description": "Voyage number"
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Maximum results to return",
                            "default": 50
                        }
                    }
                }
            },
            {
                "name": "get_vessel_schedule",
                "description": "Get vessel schedule and voyage information",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "vessel_name": {
                            "type": "string",
                            "description": "Name of the vessel"
                        },
                        "voyage_number": {
                            "type": "string",
                            "description": "Voyage number"
                        }
                    }
                }
            }
        ]

    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Call a specific MCP tool."""
        if tool_name == "get_container_status":
            return await self._get_container_status(arguments)
        elif tool_name == "get_bl_status":
            return await self._get_bl_status(arguments)
        elif tool_name == "search_shipments":
            return await self._search_shipments(arguments)
        elif tool_name == "get_vessel_schedule":
            return await self._get_vessel_schedule(arguments)
        else:
            return [{"error": f"Unknown tool: {tool_name}"}]

    async def _get_container_status(self, arguments: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Get container status from CMA CGM."""
        container_id = arguments.get("container_id")

        if not container_id:
            return [{"error": "container_id is required"}]

        try:
            # Call CMA CGM API
            raw_data = await self.api_service.get_container_from_cma_cgm(container_id)

            if not raw_data:
                return [{"error": "Container not found or API unavailable"}]

            # Format response
            formatted_data = self.api_service.format_container_data(raw_data)

            return [{
                "container_id": container_id,
                "status": formatted_data["status"],
                "vessel": formatted_data.get("vessel", ""),
                "voyage": formatted_data.get("voyage", ""),
                "estimated_arrival": formatted_data.get("estimatedArrival", ""),
                "last_updated": formatted_data["lastUpdated"]
            }]

        except Exception as e:
            return [{"error": f"Failed to get container status: {str(e)}"}]

    async def _get_bl_status(self, arguments: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Get bill of lading status from CMA CGM."""
        bl_number = arguments.get("bl_number")

        if not bl_number:
            return [{"error": "bl_number is required"}]

        try:
            # Call CMA CGM API
            raw_data = await self.api_service.get_bl_from_cma_cgm(bl_number)

            if not raw_data:
                return [{"error": "Bill of Lading not found or API unavailable"}]

            # Format response
            formatted_data = self.api_service.format_bl_data(raw_data)

            return [{
                "bl_number": bl_number,
                "status": "active",
                "vessel": formatted_data["vesselVoyage"].get("vesselName", ""),
                "voyage": formatted_data["vesselVoyage"].get("voyageNumber", ""),
                "origin": formatted_data["origin"],
                "destination": formatted_data["destination"],
                "estimated_arrival": formatted_data["estimatedArrival"],
                "containers": formatted_data["containers"]
            }]

        except Exception as e:
            return [{"error": f"Failed to get BL status: {str(e)}"}]

    async def _search_shipments(self, arguments: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Search shipments by criteria."""
        origin = arguments.get("origin")
        destination = arguments.get("destination")
        vessel = arguments.get("vessel")
        voyage = arguments.get("voyage")
        limit = arguments.get("limit", 50)

        try:
            # In a real implementation, this would call the CMA CGM search API
            # For now, return mock data
            shipments = [
                {
                    "bl_number": "ABC1234567",
                    "vessel": "Marco Polo",
                    "voyage": "12345",
                    "origin": "Lagos",
                    "destination": "Ikorodu",
                    "status": "in_transit",
                    "estimated_arrival": "2025-01-20T10:00:00Z"
                },
                {
                    "bl_number": "ABC1234568",
                    "vessel": "Columbus",
                    "voyage": "67890",
                    "origin": "Lagos",
                    "destination": "Apapa",
                    "status": "at_terminal",
                    "estimated_arrival": "2025-01-18T14:00:00Z"
                }
            ][:limit]

            # Apply filters
            filtered_shipments = shipments

            if origin:
                filtered_shipments = [s for s in filtered_shipments if s["origin"].lower() == origin.lower()]

            if destination:
                filtered_shipments = [s for s in filtered_shipments if s["destination"].lower() == destination.lower()]

            if vessel:
                filtered_shipments = [s for s in filtered_shipments if vessel.lower() in s["vessel"].lower()]

            if voyage:
                filtered_shipments = [s for s in filtered_shipments if voyage in s["voyage"]]

            return [{
                "search_criteria": {
                    "origin": origin,
                    "destination": destination,
                    "vessel": vessel,
                    "voyage": voyage,
                    "limit": limit
                },
                "shipments": filtered_shipments,
                "total_found": len(filtered_shipments)
            }]

        except Exception as e:
            return [{"error": f"Failed to search shipments: {str(e)}"}]

    async def _get_vessel_schedule(self, arguments: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Get vessel schedule and voyage information."""
        vessel_name = arguments.get("vessel_name")
        voyage_number = arguments.get("voyage_number")

        try:
            # In a real implementation, this would call the CMA CGM vessel schedule API
            # For now, return mock data
            schedule = {
                "vessel_name": vessel_name or "Marco Polo",
                "voyage_number": voyage_number or "12345",
                "current_status": "in_transit",
                "current_location": "Atlantic Ocean",
                "next_port": "Ikorodu",
                "estimated_arrival": "2025-01-20T10:00:00Z",
                "route": [
                    {"port": "Lagos", "departure": "2025-01-15T08:00:00Z"},
                    {"port": "Ikorodu", "arrival": "2025-01-20T10:00:00Z"}
                ]
            }

            return [schedule]

        except Exception as e:
            return [{"error": f"Failed to get vessel schedule: {str(e)}"}]

    async def get_server_info(self) -> Dict[str, Any]:
        """Get MCP server information."""
        return {
            "name": "CMA CGM MCP Server",
            "version": "1.0.0",
            "description": "MCP server for CMA CGM API integration",
            "capabilities": {
                "tools": len(self.get_tools()),
                "streaming": False
            }
        }
