"""Agent Registry and Capability Registry.

The discovery layer: every robot, agent, sensor, and tool registers itself
at runtime so the Swarm can reason over the live topology.
"""

from __future__ import annotations

import threading
from typing import Dict, List, Optional

from rosclaw_swarm.models import AgentCapabilities, Capability


class AgentRegistry:
    """Runtime directory of all swarm participants.

    Analogous to Kubernetes Service Discovery — but for robots, sensors,
    agents, and tools.
    """

    def __init__(self) -> None:
        self._agents: Dict[str, AgentCapabilities] = {}
        self._lock = threading.RLock()

    def register(self, agent: AgentCapabilities) -> None:
        with self._lock:
            self._agents[agent.agent_id] = agent

    def unregister(self, agent_id: str) -> None:
        with self._lock:
            self._agents.pop(agent_id, None)

    def get(self, agent_id: str) -> Optional[AgentCapabilities]:
        with self._lock:
            return self._agents.get(agent_id)

    def list_all(self) -> List[AgentCapabilities]:
        with self._lock:
            return list(self._agents.values())

    def find(self, capability: str) -> List[AgentCapabilities]:
        """Return all agents that declare *capability*."""
        with self._lock:
            return [
                a for a in self._agents.values()
                if any(c.name == capability for c in a.capabilities)
            ]

    def update_pose(self, agent_id: str, pose: Dict[str, float]) -> None:
        with self._lock:
            if agent_id in self._agents:
                self._agents[agent_id].pose = pose

    def update_battery(self, agent_id: str, level: float) -> None:
        with self._lock:
            if agent_id in self._agents:
                self._agents[agent_id].battery_level = level

    def update_load(self, agent_id: str, load: float) -> None:
        with self._lock:
            if agent_id in self._agents:
                self._agents[agent_id].load = load


class CapabilityRegistry:
    """Capability Graph — links Agent → Capability → Skill → Experience.

    This is the most critical infrastructure for swarm scheduling.
    The scheduler asks not "who claims they can?" but "who historically
    succeeds at it?" — that success rate lives here.
    """

    def __init__(self) -> None:
        # agent_id -> {capability_name: Capability}
        self._graph: Dict[str, Dict[str, Capability]] = {}
        self._lock = threading.RLock()

    def upsert(self, agent_id: str, capability: Capability) -> None:
        with self._lock:
            self._graph.setdefault(agent_id, {})[capability.name] = capability

    def get(self, agent_id: str, capability_name: str) -> Optional[Capability]:
        with self._lock:
            return self._graph.get(agent_id, {}).get(capability_name)

    def agent_capabilities(self, agent_id: str) -> List[Capability]:
        with self._lock:
            return list(self._graph.get(agent_id, {}).values())

    def all_for_capability(self, capability_name: str) -> Dict[str, Capability]:
        """Map agent_id -> Capability for a given capability name."""
        with self._lock:
            return {
                agent_id: caps[capability_name]
                for agent_id, caps in self._graph.items()
                if capability_name in caps
            }

    def update_success_rate(self, agent_id: str, capability_name: str, success_rate: float) -> None:
        with self._lock:
            caps = self._graph.setdefault(agent_id, {})
            if capability_name in caps:
                caps[capability_name].success_rate = success_rate
            else:
                caps[capability_name] = Capability(
                    name=capability_name, success_rate=success_rate
                )

    def best_agent(self, capability_name: str) -> Optional[str]:
        """Return the agent_id with the highest success_rate for a capability."""
        with self._lock:
            candidates = self.all_for_capability(capability_name)
            if not candidates:
                return None
            return max(candidates, key=lambda a: candidates[a].success_rate)
