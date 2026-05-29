"""Safety Zone — Shared safety region broadcast among swarm agents.

Each agent publishes its safety envelope.  The swarm computes the
intersection / exclusion zones to prevent inter-robot collision during
cooperative tasks.
"""

from __future__ import annotations

import time
from typing import Any, Dict, List, Optional


class SafetyZone:
    """A spherical or AABB safety envelope around an agent."""

    def __init__(
        self,
        agent_id: str,
        radius_m: float = 0.5,
        center_m: Optional[Dict[str, float]] = None,
        zone_type: str = "exclusion",
    ) -> None:
        self.agent_id = agent_id
        self.radius_m = radius_m
        self.center_m = center_m or {"x": 0.0, "y": 0.0, "z": 0.0}
        self.zone_type = zone_type
        self.timestamp = time.time()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "agent_id": self.agent_id,
            "radius_m": self.radius_m,
            "center_m": self.center_m,
            "zone_type": self.zone_type,
            "timestamp": self.timestamp,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SafetyZone":
        return cls(
            agent_id=data["agent_id"],
            radius_m=data.get("radius_m", 0.5),
            center_m=data.get("center_m"),
            zone_type=data.get("zone_type", "exclusion"),
        )

    def check_overlap(self, other: "SafetyZone", my_pose: Dict[str, float], other_pose: Dict[str, float]) -> bool:
        """Return True if two safety zones overlap in world frame."""
        cx1 = my_pose.get("x", 0.0) + self.center_m.get("x", 0.0)
        cy1 = my_pose.get("y", 0.0) + self.center_m.get("y", 0.0)
        cz1 = my_pose.get("z", 0.0) + self.center_m.get("z", 0.0)
        cx2 = other_pose.get("x", 0.0) + other.center_m.get("x", 0.0)
        cy2 = other_pose.get("y", 0.0) + other.center_m.get("y", 0.0)
        cz2 = other_pose.get("z", 0.0) + other.center_m.get("z", 0.0)
        dist = ((cx1 - cx2) ** 2 + (cy1 - cy2) ** 2 + (cz1 - cz2) ** 2) ** 0.5
        return dist < (self.radius_m + other.radius_m)


class SafetyZoneManager:
    """Aggregates safety zones from all swarm agents and computes conflicts."""

    def __init__(self) -> None:
        self._zones: Dict[str, SafetyZone] = {}

    def update_zone(self, agent_id: str, zone: SafetyZone) -> None:
        self._zones[agent_id] = zone

    def remove_zone(self, agent_id: str) -> None:
        self._zones.pop(agent_id, None)

    def get_zone(self, agent_id: str) -> Optional[SafetyZone]:
        return self._zones.get(agent_id)

    def check_all_conflicts(
        self,
        poses: Dict[str, Dict[str, float]],
    ) -> List[Dict[str, Any]]:
        """Return list of overlapping zone pairs."""
        conflicts = []
        agent_ids = list(self._zones.keys())
        for i, a1 in enumerate(agent_ids):
            for a2 in agent_ids[i + 1 :]:
                z1 = self._zones.get(a1)
                z2 = self._zones.get(a2)
                p1 = poses.get(a1)
                p2 = poses.get(a2)
                if z1 and z2 and p1 and p2 and z1.check_overlap(z2, p1, p2):
                    dist = ((p1["x"] - p2["x"]) ** 2 + (p1["y"] - p2["y"]) ** 2 + (p1["z"] - p2["z"]) ** 2) ** 0.5
                    conflicts.append({
                        "agent_1": a1,
                        "agent_2": a2,
                        "distance": dist,
                        "combined_radius": z1.radius_m + z2.radius_m,
                    })
        return conflicts

    def export_state(self) -> Dict[str, Any]:
        return {
            agent_id: zone.to_dict()
            for agent_id, zone in self._zones.items()
        }
