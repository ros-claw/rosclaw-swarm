"""Force State Share — distributes force/wrench data among swarm agents.

P1 feature for cooperative manipulation.  When two agents jointly carry
an object, each shares its local force sensor readings so the partner
can compensate and prevent load imbalance.
"""

from __future__ import annotations

import time
from typing import Any, Dict, List, Optional


class ForceState:
    """Snapshot of an agent's force/torque state."""

    def __init__(
        self,
        agent_id: str,
        wrench: Optional[Dict[str, Any]] = None,
        joint_torques: Optional[List[float]] = None,
        load_ratio: float = 0.0,
    ) -> None:
        self.agent_id = agent_id
        self.wrench = wrench or {"force": {"x": 0.0, "y": 0.0, "z": 0.0}, "torque": {"x": 0.0, "y": 0.0, "z": 0.0}}
        self.joint_torques = joint_torques or []
        self.load_ratio = load_ratio
        self.timestamp = time.time()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "agent_id": self.agent_id,
            "wrench": self.wrench,
            "joint_torques": self.joint_torques,
            "load_ratio": self.load_ratio,
            "timestamp": self.timestamp,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ForceState":
        return cls(
            agent_id=data["agent_id"],
            wrench=data.get("wrench"),
            joint_torques=data.get("joint_torques"),
            load_ratio=data.get("load_ratio", 0.0),
        )


class ForceStateShare:
    """Aggregates force state from all swarm agents."""

    def __init__(self) -> None:
        self._states: Dict[str, ForceState] = {}

    def update(self, agent_id: str, state: ForceState) -> None:
        self._states[agent_id] = state

    def remove(self, agent_id: str) -> None:
        self._states.pop(agent_id, None)

    def get(self, agent_id: str) -> Optional[ForceState]:
        return self._states.get(agent_id)

    def compute_load_imbalance(self) -> Dict[str, float]:
        """Return per-agent deviation from equal load sharing."""
        if not self._states:
            return {}
        n = len(self._states)
        target = 1.0 / n
        return {
            agent_id: state.load_ratio - target
            for agent_id, state in self._states.items()
        }

    def detect_overload(self, threshold: float = 0.8) -> List[str]:
        """Return list of agent_ids exceeding load threshold."""
        return [
            agent_id
            for agent_id, state in self._states.items()
            if state.load_ratio > threshold
        ]

    def export_state(self) -> Dict[str, Any]:
        return {
            agent_id: state.to_dict()
            for agent_id, state in self._states.items()
        }
