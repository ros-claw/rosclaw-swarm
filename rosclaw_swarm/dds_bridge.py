"""DDS Bridge — manages high-frequency ROS 2 QoS communication.

The micro reflex plane runs on raw DDS, not through Python serialization.
This module configures the QoS profiles and provides Python-side helpers
for topic management.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass
class QoSProfile:
    """Mirror of rclpy.qos.QoSProfile for environments without ROS 2 installed."""

    reliability: str = "best_effort"  # best_effort | reliable
    durability: str = "volatile"      # volatile | transient_local
    history: str = "keep_last"        # keep_last | keep_all
    depth: int = 1
    deadline_ms: Optional[int] = None
    lifespan_ms: Optional[int] = None


REFLEX_QOS = QoSProfile(
    reliability="best_effort",
    durability="volatile",
    history="keep_last",
    depth=1,
)

"""
When rclpy is available, replace the above with:

from rclpy.qos import QoSProfile, ReliabilityPolicy, HistoryPolicy, DurabilityPolicy

def get_reflex_qos_profile():
    return QoSProfile(
        reliability=ReliabilityPolicy.BEST_EFFORT,
        durability=DurabilityPolicy.VOLATILE,
        history=HistoryPolicy.KEEP_LAST,
        depth=1,
    )
"""


def reflex_topic(agent_id: str) -> str:
    return f"/rosclaw/swarm/{agent_id}/reflex"


def intent_topic(swarm_session_id: str) -> str:
    return f"/rosclaw/swarm/{swarm_session_id}/intent"


def handoff_topic(swarm_session_id: str, handoff_id: str) -> str:
    return f"/rosclaw/swarm/{swarm_session_id}/handoff/{handoff_id}"
