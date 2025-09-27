"""MCP server for EFL Terminal API integration."""

import asyncio
from typing import Dict, List, Any, Optional

from src.core.config import settings
from src.services.external_api_service import ExternalAPIService


class EFLTerminalMCPServer:
    """MCP server for EFL Terminal API integration."""

    def __init__(self):
        self.api_service = None
        self._tools = {}

    async def get_instance(self) -> "EFLTerminalMCPServer":
        """Get singleton instance with dependencies initialized."""
        if self.api_service is None:
            self.api_service = await ExternalAPIService().get_instance()
        return self

    def get_tools(self) -> List[Dict[str, Any]]:
        """Get list of available MCP tools."""
        return [
            {
                "name": "get_container_status",
                "description": "Get current status of a container from EFL Terminal",
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
                "name": "get_container_milestones",
                "description": "Get milestone history for a container",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "container_id": {
                            "type": "string",
                            "description": "Container ID"
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Maximum number of milestones to return",
                            "default": 20
                        }
                    },
                    "required": ["container_id"]
                }
            },
            {
                "name": "search_containers",
                "description": "Search containers by various criteria",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "agent_id": {
                            "type": "string",
                            "description": "Agent ID for filtering"
                        },
                        "status": {
                            "type": "string",
                            "description": "Container status filter"
                        },
                        "location": {
                            "type": "string",
                            "description": "Location filter"
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Maximum results to return",
                            "default": 50
                        }
                    }
                }
            }
        ]

    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Call a specific MCP tool."""
        if tool_name == "get_container_status":
            return await self._get_container_status(arguments)
        elif tool_name == "get_container_milestones":
            return await self._get_container_milestones(arguments)
        elif tool_name == "search_containers":
            return await self._search_containers(arguments)
        else:
            return [{"error": f"Unknown tool: {tool_name}"}]

    async def _get_container_status(self, arguments: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Get container status from EFL Terminal."""
        container_id = arguments.get("container_id")

        if not container_id:
            return [{"error": "container_id is required"}]

        try:
            # Call EFL Terminal API
            raw_data = await self.api_service.get_container_from_efl_terminal(container_id)

            if not raw_data:
                return [{"error": "Container not found or API unavailable"}]

            # Format response
            formatted_data = self.api_service.format_container_data(raw_data)

            return [{
                "container_id": container_id,
                "status": formatted_data["status"],
                "location": formatted_data["location"],
                "last_updated": formatted_data["lastUpdated"],
                "next_step": formatted_data["nextStep"]
            }]

        except Exception as e:
            return [{"error": f"Failed to get container status: {str(e)}"}]

    async def _get_container_milestones(self, arguments: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Get container milestones from EFL Terminal."""
        container_id = arguments.get("container_id")
        limit = arguments.get("limit", 20)

        if not container_id:
            return [{"error": "container_id is required"}]

        try:
            # In a real implementation, this would call the EFL Terminal milestones API
            # For now, return mock data
            milestones = [
                {
                    "event_type": "discharged",
                    "location": "Yard A1",
                    "timestamp": "2025-01-15T10:00:00Z",
                    "description": "Container discharged from vessel"
                },
                {
                    "event_type": "gate_in",
                    "location": "Gate 1",
                    "timestamp": "2025-01-15T11:00:00Z",
                    "description": "Container entered terminal"
                }
            ][:limit]

            return [{
                "container_id": container_id,
                "milestones": milestones
            }]

        except Exception as e:
            return [{"error": f"Failed to get container milestones: {str(e)}"}]

    async def _search_containers(self, arguments: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Search containers based on criteria."""
        agent_id = arguments.get("agent_id")
        status = arguments.get("status")
        location = arguments.get("location")
        limit = arguments.get("limit", 50)

        try:
            # In a real implementation, this would call the EFL Terminal search API
            # For now, return mock data
            containers = [
                {
                    "container_id": "EFLU7896543",
                    "status": "at_terminal",
                    "location": "Yard A1",
                    "last_updated": "2025-01-15T12:00:00Z"
                },
                {
                    "container_id": "EFLU7896544",
                    "status": "in_transit",
                    "location": "On Vessel",
                    "last_updated": "2025-01-15T11:30:00Z"
                }
            ][:limit]

            # Apply filters
            filtered_containers = containers

            if status:
                filtered_containers = [c for c in filtered_containers if c["status"] == status]

            if location:
                filtered_containers = [c for c in filtered_containers if location.lower() in c["location"].lower()]

            return [{
                "search_criteria": {
                    "agent_id": agent_id,
                    "status": status,
                    "location": location,
                    "limit": limit
                },
                "containers": filtered_containers,
                "total_found": len(filtered_containers)
            }]

        except Exception as e:
            return [{"error": f"Failed to search containers: {str(e)}"}]

    async def get_server_info(self) -> Dict[str, Any]:
        """Get MCP server information."""
        return {
            "name": "EFL Terminal MCP Server",
            "version": "1.0.0",
            "description": "MCP server for EFL Terminal API integration",
            "capabilities": {
                "tools": len(self.get_tools()),
                "streaming": False
            }
        }
