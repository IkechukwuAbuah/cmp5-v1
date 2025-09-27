"""AgentService for agent validation and permissions management."""

from typing import Dict, List, Optional
from src.models.agent import Agent, Permission


class AgentService:
    """Service for managing agent validation and permissions."""

    def __init__(self):
        # In a real implementation, this would load from a database
        self._agents: Dict[str, Agent] = {}

    def get_agent(self, agent_id: str) -> Optional[Agent]:
        """Get agent by ID."""
        return self._agents.get(agent_id)

    def authenticate_agent(self, agent_id: str, credentials: Dict) -> Optional[Agent]:
        """Authenticate agent with credentials."""
        # This would typically verify against a database or external system
        # For now, create a mock agent if it doesn't exist
        if agent_id not in self._agents:
            self._create_mock_agent(agent_id)

        agent = self._agents[agent_id]

        # Check if agent is active
        if not agent.isActive:
            return None

        # In a real implementation, verify credentials here
        return agent

    def validate_permissions(self, agent: Agent, resource: str, action: str) -> bool:
        """Validate if agent has permission for resource and action."""
        return agent.has_permission(resource, action)

    def can_access_container(self, agent: Agent, container_id: str) -> bool:
        """Check if agent can access a specific container."""
        # In a real implementation, this would check against a database
        # For now, use the agent's permission system
        return agent.can_access_container(container_id)

    def can_access_bl(self, agent: Agent, bl_number: str) -> bool:
        """Check if agent can access a specific bill of lading."""
        # In a real implementation, this would check against a database
        # For now, use the agent's permission system
        return agent.can_access_bl(bl_number)

    def get_agent_containers(self, agent: Agent) -> List[str]:
        """Get list of containers accessible by agent."""
        # In a real implementation, this would query a database
        # For now, return empty list
        return []

    def get_agent_bls(self, agent: Agent) -> List[str]:
        """Get list of bill of ladings accessible by agent."""
        # In a real implementation, this would query a database
        # For now, return empty list
        return []

    def update_agent_permissions(self, agent_id: str, permissions: List[Permission]) -> bool:
        """Update agent's permissions."""
        agent = self.get_agent(agent_id)

        if not agent:
            return False

        agent.permissions = permissions
        return True

    def _create_mock_agent(self, agent_id: str):
        """Create a mock agent for testing."""
        from src.models.agent import ContactInfo

        agent = Agent(
            id=agent_id,
            name=f"Agent {agent_id}",
            type="clearing",
            contactInfo=ContactInfo(
                phone="+234-123-4567",
                email=f"{agent_id}@efl.com",
                companyName="EFL Clearing Agency"
            ),
            permissions=[
                Permission(
                    resource="container",
                    actions=["read", "track", "view_milestones"],
                    conditions=[]
                ),
                Permission(
                    resource="bl",
                    actions=["read", "track"],
                    conditions=[]
                ),
                Permission(
                    resource="session",
                    actions=["create", "read", "update"],
                    conditions=[]
                )
            ]
        )

        self._agents[agent_id] = agent

    def get_all_agents(self) -> List[Agent]:
        """Get all agents."""
        return list(self._agents.values())

    def get_agent_stats(self) -> Dict:
        """Get agent statistics."""
        total_agents = len(self._agents)
        active_agents = len([a for a in self._agents.values() if a.isActive])

        return {
            "total_agents": total_agents,
            "active_agents": active_agents
        }
