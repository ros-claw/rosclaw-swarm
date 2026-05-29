"""TF Sync — Shared coordinate frame synchronisation between swarm agents.

All agents in a swarm session share a unified world frame.  The leader
broadcasts the shared frame; followers mount their base frames under it.
"""

from __future__ import annotations

import time
from typing import Any, Dict, List, Optional

from rosclaw_swarm.models import AgentCapabilities, SwarmContext


class TFSync:
    """Manages the shared TF tree for a swarm session.

    Usage:
        tf = TFSync(session_id="swarm_001", shared_frame="swarm_world_001")
        tf.register_agent("g1", base_frame="g1_base", pose={"x": 1.0, "y": 0.0, "z": 0.0})
        tf.register_agent("ur5", base_frame="ur5_base", pose={"x": 2.0, "y": 0.0, "z": 0.0})
        # Broadcast handoff point in shared frame
        tf.set_handoff_point("lift_point", {"x": 1.5, "y": 0.0, "z": 0.5})
    """

    def __init__(
        self,
        session_id: str,
        shared_frame: str = "swarm_world_001",
    ) -> None:
        self.session_id = session_id
        self.shared_frame = shared_frame
        # agent_id -> base_frame name
        self._agent_frames: Dict[str, str] = {}
        # agent_id -> pose in shared frame
        self._agent_poses: Dict[str, Dict[str, float]] = {}
        # Named points of interest in shared frame
        self._handoff_points: Dict[str, Dict[str, float]] = {}
        self._last_update: float = 0.0

    def register_agent(
        self,
        agent_id: str,
        base_frame: str,
        pose: Optional[Dict[str, float]] = None,
    ) -> None:
        """Mount an agent's base frame under the shared world frame."""
        self._agent_frames[agent_id] = base_frame
        self._agent_poses[agent_id] = pose or {"x": 0.0, "y": 0.0, "z": 0.0}
        self._last_update = time.time()

    def update_agent_pose(self, agent_id: str, pose: Dict[str, float]) -> None:
        """Update an agent's pose in the shared frame."""
        if agent_id in self._agent_frames:
            self._agent_poses[agent_id] = pose
            self._last_update = time.time()

    def set_handoff_point(self, name: str, pose: Dict[str, float]) -> None:
        """Define a named 3D point in the shared frame (e.g. lift point)."""
        self._handoff_points[name] = pose
        self._last_update = time.time()

    def get_handoff_point(self, name: str) -> Optional[Dict[str, float]]:
        return self._handoff_points.get(name)

    def list_handoff_points(self) -> Dict[str, Dict[str, float]]:
        return dict(self._handoff_points)

    def get_agent_pose(self, agent_id: str) -> Optional[Dict[str, float]]:
        return self._agent_poses.get(agent_id)

    def get_relative_pose(
        self,
        from_agent_id: str,
        to_agent_id: str,
    ) -> Optional[Dict[str, float]]:
        """Compute pose of to_agent relative to from_agent."""
        p1 = self._agent_poses.get(from_agent_id)
        p2 = self._agent_poses.get(to_agent_id)
        if not p1 or not p2:
            return None
        return {
            "x": p2["x"] - p1["x"],
            "y": p2["y"] - p1["y"],
            "z": p2["z"] - p1["z"],
        }

    def export_state(self) -> Dict[str, Any]:
        """Snapshot of the entire TF tree for persistence / MCAP."""
        return {
            "session_id": self.session_id,
            "shared_frame": self.shared_frame,
            "agent_frames": dict(self._agent_frames),
            "agent_poses": dict(self._agent_poses),
            "handoff_points": dict(self._handoff_points),
            "last_update": self._last_update,
        }

    @classmethod
    def from_swarm_context(cls, ctx: SwarmContext) -> "TFSync":
        """Build a TFSync from an existing SwarmContext."""
        tf = cls(
            session_id=ctx.swarm_session_id,
            shared_frame=ctx.shared_world_frame,
        )
        for agent in ctx.topology:
            tf.register_agent(
                agent_id=agent.agent_id,
                base_frame=f"{agent.agent_id}_base",
                pose=agent.pose,
            )
        return tf
