"""Swarm Scheduler — selects the best agent for each task.

The brain of the macro control plane.  Uses the Capability Graph and
real-time telemetry (pose, battery, load, risk) to score candidates.
"""

from __future__ import annotations

from typing import Dict, List, Optional, Tuple

from rosclaw_swarm.models import AgentCapabilities, Capability, Task
from rosclaw_swarm.registry import AgentRegistry, CapabilityRegistry


class SwarmScheduler:
    """Capability-aware scheduler with multi-factor scoring."""

    def __init__(
        self,
        agent_registry: AgentRegistry,
        capability_registry: CapabilityRegistry,
    ) -> None:
        self.agents = agent_registry
        self.caps = capability_registry

    def score(
        self,
        agent: AgentCapabilities,
        capability: Capability,
        task_location: Optional[Tuple[float, float, float]] = None,
    ) -> float:
        """Compute a composite score for an agent executing a capability.

        score = success_rate + proximity_bonus - risk_penalty - load_penalty
        """
        score = capability.success_rate

        if agent.battery_level is not None and agent.battery_level < 0.2:
            score -= 0.5  # critically low battery

        if agent.load is not None:
            score -= agent.load * 0.3  # penalise high load

        score -= agent.risk_score * 0.4

        if task_location and agent.pose:
            try:
                ax, ay, az = agent.pose.get("x", 0), agent.pose.get("y", 0), agent.pose.get("z", 0)
                tx, ty, tz = task_location
                dist = ((ax - tx) ** 2 + (ay - ty) ** 2 + (az - tz) ** 2) ** 0.5
                proximity_bonus = max(0.0, 1.0 - dist / 10.0)  # 10m scale
                score += proximity_bonus * 0.2
            except Exception:
                pass

        return score

    def select_best_agent(
        self,
        task: Task,
        task_location: Optional[Tuple[float, float, float]] = None,
    ) -> Optional[str]:
        """Return the agent_id with the highest composite score for *task*."""
        if not task.capability:
            return None

        candidates = self.agents.find(task.capability)
        if not candidates:
            return None

        best: Optional[str] = None
        best_score = -float("inf")

        for agent in candidates:
            cap = self.caps.get(agent.agent_id, task.capability)
            if cap is None:
                cap = Capability(name=task.capability, success_rate=0.5)
            s = self.score(agent, cap, task_location)
            if s > best_score:
                best_score = s
                best = agent.agent_id

        return best

    def schedule_graph(self, task_graph, task_locations: Optional[Dict[str, Tuple[float, float, float]]] = None) -> Dict[str, Optional[str]]:
        """Schedule every ready task in the graph.

        Returns a mapping of task_id -> assigned_agent_id (or None if no
        capable agent was found).
        """
        assignments: Dict[str, Optional[str]] = {}
        locs = task_locations or {}

        for task in task_graph.ready_tasks():
            agent_id = self.select_best_agent(task, locs.get(task.id))
            if agent_id:
                assignments[task.id] = agent_id

        return assignments
