"""Physical Reflex Handshake — Force-Feedback Sync.

The soul of rosclaw-swarm.  Once the macro control plane assigns roles,
this module takes over and runs at 1000Hz without LLM involvement.
"""

from __future__ import annotations

import asyncio
from enum import Enum
from typing import Any, Callable, Dict, Optional

from rosclaw_swarm.models import SwarmReflexMessage


class ReflexPhase(str, Enum):
    APPROACH = "approach"
    CONTACT = "contact"
    EXECUTE = "execute"
    RELEASE = "release"
    ABORT = "abort"


class ReflexHandshake:
    """State machine for physical handoff between two agents.

    Example: G1 (supplier) passes a part to UR5 (receiver).
    Both agents publish SwarmReflexMessage at 200-1000Hz and react to
    force-threshold crossings to transition phases.
    """

    def __init__(
        self,
        my_agent_id: str,
        peer_agent_id: str,
        my_role: str,          # "supplier" | "receiver" | "leader" | "follower"
        force_threshold: float = 2.5,
        latency_threshold_ms: float = 5.0,
        on_phase_change: Optional[Callable[[ReflexPhase], None]] = None,
        on_emergency: Optional[Callable[[str], None]] = None,
    ) -> None:
        self.my_agent_id = my_agent_id
        self.peer_agent_id = peer_agent_id
        self.my_role = my_role
        self.force_threshold = force_threshold
        self.latency_threshold_ms = latency_threshold_ms
        self.phase = ReflexPhase.APPROACH
        self.on_phase_change = on_phase_change
        self.on_emergency = on_emergency

        # Latest state from peer
        self._peer_msg: Optional[SwarmReflexMessage] = None
        self._local_force: float = 0.0

    def receive_peer_reflex(self, msg: SwarmReflexMessage, local_stamp_ns: int) -> None:
        """Process incoming reflex message from peer."""
        latency_ms = (local_stamp_ns - msg.stamp_ns) / 1e6
        if latency_ms > self.latency_threshold_ms:
            self._trigger_emergency(f"Latency exceeded: {latency_ms:.2f}ms")
            return

        self._peer_msg = msg

    def update_local_force(self, force: float) -> None:
        """Feed local force-sensor reading (1000Hz)."""
        self._local_force = force
        if self.phase == ReflexPhase.APPROACH and force > self.force_threshold:
            self._transition(ReflexPhase.CONTACT)

    async def wait_for_physical_contact(self, read_sensor: Callable[[], float]) -> bool:
        """Blocking poll until physical contact detected.

        In a real deployment this is replaced by an interrupt-driven
        hardware callback; the asyncio loop here is for simulation/tests.
        """
        while self.phase != ReflexPhase.CONTACT:
            current_force = read_sensor()
            self.update_local_force(current_force)
            if current_force > self.force_threshold:
                return True
            await asyncio.sleep(0.001)  # 1000Hz poll
        return True

    def _transition(self, new_phase: ReflexPhase) -> None:
        if self.phase != new_phase:
            self.phase = new_phase
            if self.on_phase_change:
                self.on_phase_change(new_phase)

    def _trigger_emergency(self, reason: str) -> None:
        self.phase = ReflexPhase.ABORT
        if self.on_emergency:
            self.on_emergency(reason)

    def compute_compensation(self) -> Optional[Dict[str, Any]]:
        """Calculate adjustment command based on peer reflex.

        If peer (e.g. G1) moved, return a velocity/position correction
        for the local agent (e.g. UR5) to prevent tearing the object.
        """
        if self._peer_msg is None:
            return None
        # Stub: real implementation uses TF tree + Jacobian IK
        return {
            "source": self.peer_agent_id,
            "compensation_linear": [0.0, 0.0, 0.0],
            "compensation_angular": [0.0, 0.0, 0.0],
        }
