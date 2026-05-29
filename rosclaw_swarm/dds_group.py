"""DDS Group Manager — forms multicast groups and manages topic namespaces.

When a swarm session is formed, all agents join a shared DDS domain.
This module computes topic names, manages the group lifecycle, and
ensures no topic collisions between different swarm sessions.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Set


class DDSGroupManager:
    """Manages DDS topics and group membership for a swarm session."""

    def __init__(
        self,
        session_id: str,
        domain_id: int = 42,
    ) -> None:
        self.session_id = session_id
        self.domain_id = domain_id
        self._agents: Set[str] = set()
        self._handoff_counter = 0

    def add_agent(self, agent_id: str) -> None:
        self._agents.add(agent_id)

    def remove_agent(self, agent_id: str) -> None:
        self._agents.discard(agent_id)

    def list_agents(self) -> List[str]:
        return sorted(self._agents)

    def reflex_topic(self, agent_id: str) -> str:
        """Per-agent high-frequency reflex topic."""
        return f"/rosclaw/swarm/{self.session_id}/{agent_id}/reflex"

    def intent_topic(self) -> str:
        """Shared intent broadcast topic for the group."""
        return f"/rosclaw/swarm/{self.session_id}/intent"

    def handoff_topic(self, handoff_id: Optional[str] = None) -> str:
        """Per-handoff coordination topic."""
        if handoff_id is None:
            self._handoff_counter += 1
            handoff_id = f"h_{self._handoff_counter:04d}"
        return f"/rosclaw/swarm/{self.session_id}/handoff/{handoff_id}"

    def safety_topic(self) -> str:
        """Shared safety zone broadcast topic."""
        return f"/rosclaw/swarm/{self.session_id}/safety"

    def tf_topic(self) -> str:
        """Shared TF tree broadcast topic."""
        return f"/rosclaw/swarm/{self.session_id}/tf"

    def state_topic(self) -> str:
        """Shared state topic for practice timeline sync."""
        return f"/rosclaw/swarm/{self.session_id}/state"

    def all_topics(self) -> Dict[str, str]:
        """Return all topics managed by this group."""
        return {
            "intent": self.intent_topic(),
            "safety": self.safety_topic(),
            "tf": self.tf_topic(),
            "state": self.state_topic(),
        }

    def dissolve(self) -> Dict[str, Any]:
        """Return dissolution manifest — topics to unsubscribe, agents to release."""
        manifest = {
            "session_id": self.session_id,
            "domain_id": self.domain_id,
            "agents": list(self._agents),
            "topics": self.all_topics(),
        }
        self._agents.clear()
        return manifest

    def export_state(self) -> Dict[str, Any]:
        return {
            "session_id": self.session_id,
            "domain_id": self.domain_id,
            "agents": list(self._agents),
            "topics": self.all_topics(),
        }
