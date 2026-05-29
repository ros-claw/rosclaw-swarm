"""Role Assigner — assigns leader/follower/observer roles to swarm agents.

Based on capability analysis and task requirements, each agent gets a
role that determines its responsibilities during cooperative execution.
"""

from __future__ import annotations

from enum import Enum
from typing import Dict, List, Optional

from rosclaw_swarm.models import AgentCapabilities, TaskGraph


class SwarmRole(str, Enum):
    LEADER = "leader"       # Plans, coordinates, broadcasts intent
    FOLLOWER = "follower"   # Executes local tasks, follows leader TF
    OBSERVER = "observer"   # Monitors, records, provides perception
    SUPPLIER = "supplier"   # Provides object (handoff source)
    RECEIVER = "receiver"   # Receives object (handoff target)


class RoleAssigner:
    """Assigns roles to agents based on task requirements and capabilities.

    Usage:
        assigner = RoleAssigner()
        roles = assigner.assign(task_graph, agents)
        # roles = {"g1": SwarmRole.LEADER, "ur5": SwarmRole.FOLLOWER}
    """

    def __init__(self) -> None:
        self._rules: Dict[str, callable] = {}

    def assign(
        self,
        task_graph: TaskGraph,
        agents: List[AgentCapabilities],
    ) -> Dict[str, SwarmRole]:
        """Return agent_id -> SwarmRole mapping for the given task."""
        if not agents:
            return {}

        for pattern, rule_fn in self._rules.items():
            if pattern.lower() in task_graph.goal.lower():
                return rule_fn(task_graph, agents)

        return self._default_assign(task_graph, agents)

    def register_rule(self, goal_pattern: str, rule_fn: callable) -> None:
        self._rules[goal_pattern] = rule_fn

    def _default_assign(
        self,
        task_graph: TaskGraph,
        agents: List[AgentCapabilities],
    ) -> Dict[str, SwarmRole]:
        """Default heuristic: highest-capability agent becomes leader."""
        roles: Dict[str, SwarmRole] = {}
        scored = []
        for agent in agents:
            score = len(agent.capabilities)
            if any(c.name == "spatial_sync" for c in agent.capabilities):
                score += 10
            if any(c.name == "perception" for c in agent.capabilities):
                score += 5
            scored.append((score, agent))

        scored.sort(key=lambda x: x[0], reverse=True)

        if len(scored) == 1:
            roles[scored[0][1].agent_id] = SwarmRole.LEADER
        elif len(scored) == 2:
            roles[scored[0][1].agent_id] = SwarmRole.LEADER
            roles[scored[1][1].agent_id] = SwarmRole.FOLLOWER
        else:
            roles[scored[0][1].agent_id] = SwarmRole.LEADER
            for _, agent in scored[1:-1]:
                roles[agent.agent_id] = SwarmRole.FOLLOWER
            roles[scored[-1][1].agent_id] = SwarmRole.OBSERVER

        return roles

    @staticmethod
    def handoff_assign(
        task_graph: TaskGraph,
        agents: List[AgentCapabilities],
    ) -> Dict[str, SwarmRole]:
        """Assign supplier/receiver for handoff tasks."""
        if len(agents) < 2:
            return {agents[0].agent_id: SwarmRole.LEADER} if agents else {}

        roles: Dict[str, SwarmRole] = {}
        for agent in agents:
            cap_names = {c.name for c in agent.capabilities}
            if "locomotion" in cap_names:
                roles[agent.agent_id] = SwarmRole.SUPPLIER
            elif "manipulation" in cap_names:
                roles[agent.agent_id] = SwarmRole.RECEIVER
            else:
                roles[agent.agent_id] = SwarmRole.OBSERVER
        return roles
