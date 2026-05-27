"""MCP Tools exposed to the LLM / Agent Runtime.

These are the ONLY high-dimensional interfaces the brain sees.
Once a tool is called, the micro reflex plane takes over and the LLM
stands by.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from rosclaw_swarm.manager import SwarmRuntimeManager
from rosclaw_swarm.models import AgentCapabilities, Capability


class SwarmMCPServer:
    """FastMCP-compatible tool collection for swarm orchestration.

    Usage (with fastmcp):
        from fastmcp import FastMCP
        mcp = FastMCP("rosclaw-swarm")
        server = SwarmMCPServer(manager)
        server.mount(mcp)
    """

    def __init__(self, manager: SwarmRuntimeManager) -> None:
        self.manager = manager

    def mount(self, mcp: Any) -> None:
        """Register tools on a FastMCP instance."""

        @mcp.tool()
        async def create_swarm_session(
            goal: str,
            agent_ids: Optional[List[str]] = None,
            dds_domain_id: int = 42,
        ) -> Dict[str, Any]:
            """Create a new swarm session for a multi-agent physical task.

            Example: "G1 and UR5 lift the heavy table to the corner"
            """
            ctx = self.manager.create_session(goal, agent_ids, dds_domain_id)
            assignments = self.manager.schedule_session(ctx.swarm_session_id)
            self.manager.activate_reflex(ctx.swarm_session_id)
            return {
                "status": "SWARM_ENGAGED",
                "session_id": ctx.swarm_session_id,
                "goal": ctx.task_graph.goal if ctx.task_graph else goal,
                "topology": [a.agent_id for a in ctx.topology],
                "assignments": assignments,
                "message": "Reflex handshake protocol active. LLM can stand by.",
            }

        @mcp.tool()
        async def find_capable_agents(capability: str) -> List[Dict[str, Any]]:
            """Discover agents that can perform a given capability."""
            agents = self.manager.find_capable_agents(capability)
            return [
                {
                    "agent_id": a.agent_id,
                    "hardware_type": a.hardware_type,
                    "capabilities": [c.name for c in a.capabilities],
                    "pose": a.pose,
                    "battery": a.battery_level,
                }
                for a in agents
            ]

        @mcp.tool()
        async def establish_swarm_handoff(
            supplier_agent_id: str,
            receiver_agent_id: str,
            handoff_item: str,
            handoff_coords: List[float],
            dds_domain_id: int = 42,
        ) -> Dict[str, Any]:
            """Establish a physical handoff session between two agents.

            After calling, the system auto-manages spatial sync, force-reflex,
            and collision avoidance.  The LLM should not issue further motion
            commands until the handoff completes.
            """
            goal = (
                f"{supplier_agent_id} hands off {handoff_item} to "
                f"{receiver_agent_id} at ({handoff_coords})"
            )
            ctx = self.manager.create_session(
                goal,
                agent_ids=[supplier_agent_id, receiver_agent_id],
                dds_domain_id=dds_domain_id,
            )
            assignments = self.manager.schedule_session(ctx.swarm_session_id)
            self.manager.activate_reflex(ctx.swarm_session_id)
            return {
                "status": "SWARM_ENGAGED",
                "session_id": ctx.swarm_session_id,
                "handoff_item": handoff_item,
                "handoff_coords": handoff_coords,
                "assignments": assignments,
                "message": "Reflex handshake protocol active. LLM can stand by.",
            }

        @mcp.tool()
        async def get_session_status(session_id: str) -> Dict[str, Any]:
            """Query the current status of a swarm session."""
            ctx = self.manager.get_session(session_id)
            if not ctx:
                return {"status": "NOT_FOUND", "session_id": session_id}

            tasks = []
            if ctx.task_graph:
                for t in ctx.task_graph.tasks:
                    tasks.append({
                        "task_id": t.id,
                        "status": t.status.value,
                        "assigned_agent": t.token.assigned_agent_id if t.token else None,
                    })

            return {
                "status": "ACTIVE",
                "session_id": session_id,
                "goal": ctx.task_graph.goal if ctx.task_graph else "",
                "tasks": tasks,
                "dds_domain_id": ctx.dds_domain_id,
            }
