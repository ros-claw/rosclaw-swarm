"""Agent Discovery — find other ROSClaw agents on the same network.

Broadcasts and listens for agent heartbeat beacons.  When a peer is
discovered it is automatically added to the AgentRegistry so the
scheduler can reason over it.
"""

from __future__ import annotations

import asyncio
import json
import time
import uuid
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional

from rosclaw_swarm.models import AgentCapabilities


@dataclass
class DiscoveryBeacon:
    """Periodic heartbeat broadcast by every agent on the swarm multicast."""

    agent_id: str
    hardware_type: str
    capabilities: List[str]
    pose: Optional[Dict[str, float]] = None
    timestamp: float = field(default_factory=time.time)
    beacon_id: str = field(default_factory=lambda: f"bc_{uuid.uuid4().hex[:8]}")

    def to_json(self) -> str:
        return json.dumps({
            "agent_id": self.agent_id,
            "hardware_type": self.hardware_type,
            "capabilities": self.capabilities,
            "pose": self.pose,
            "timestamp": self.timestamp,
            "beacon_id": self.beacon_id,
        })

    @classmethod
    def from_json(cls, raw: str) -> Optional["DiscoveryBeacon"]:
        try:
            data = json.loads(raw)
            return cls(
                agent_id=data["agent_id"],
                hardware_type=data["hardware_type"],
                capabilities=data.get("capabilities", []),
                pose=data.get("pose"),
                timestamp=data.get("timestamp", time.time()),
                beacon_id=data.get("beacon_id", "unknown"),
            )
        except Exception:
            return None


class AgentDiscovery:
    """Discovers and tracks peers on the local ROSClaw swarm.

    Usage:
        discovery = AgentDiscovery(my_agent_id="g1")
        discovery.start()
        ...
        peers = discovery.list_peers()  # List[AgentCapabilities]
    """

    def __init__(
        self,
        my_agent_id: str,
        beacon_interval_sec: float = 2.0,
        peer_timeout_sec: float = 10.0,
        on_peer_discovered: Optional[Callable[[AgentCapabilities], None]] = None,
        on_peer_lost: Optional[Callable[[str], None]] = None,
    ) -> None:
        self.my_agent_id = my_agent_id
        self.beacon_interval_sec = beacon_interval_sec
        self.peer_timeout_sec = peer_timeout_sec
        self.on_peer_discovered = on_peer_discovered
        self.on_peer_lost = on_peer_lost

        # agent_id -> (timestamp, AgentCapabilities)
        self._peers: Dict[str, tuple] = {}
        self._running = False
        self._task: Optional[asyncio.Task] = None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    async def start(self) -> None:
        """Begin broadcasting beacons and pruning stale peers."""
        self._running = True
        self._task = asyncio.create_task(self._loop())

    async def stop(self) -> None:
        """Stop the discovery loop."""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass

    def list_peers(self) -> List[AgentCapabilities]:
        """Return all currently-live peers."""
        now = time.time()
        live = []
        for agent_id, (last_seen, caps) in list(self._peers.items()):
            if now - last_seen < self.peer_timeout_sec:
                live.append(caps)
            else:
                self._peers.pop(agent_id, None)
                if self.on_peer_lost:
                    self.on_peer_lost(agent_id)
        return live

    def get_peer(self, agent_id: str) -> Optional[AgentCapabilities]:
        entry = self._peers.get(agent_id)
        if not entry:
            return None
        last_seen, caps = entry
        if time.time() - last_seen >= self.peer_timeout_sec:
            self._peers.pop(agent_id, None)
            return None
        return caps

    def receive_beacon(self, raw: str) -> None:
        """Ingest a beacon received from the network (or local EventBus)."""
        beacon = DiscoveryBeacon.from_json(raw)
        if not beacon or beacon.agent_id == self.my_agent_id:
            return

        from rosclaw_swarm.models import Capability
        caps = [
            Capability(name=c)
            for c in beacon.capabilities
        ]
        agent = AgentCapabilities(
            agent_id=beacon.agent_id,
            hardware_type=beacon.hardware_type,
            capabilities=caps,
            pose=beacon.pose,
        )

        is_new = beacon.agent_id not in self._peers
        self._peers[beacon.agent_id] = (time.time(), agent)

        if is_new and self.on_peer_discovered:
            self.on_peer_discovered(agent)

    def build_beacon(self, my_capabilities: AgentCapabilities) -> str:
        """Build a beacon payload for this agent."""
        beacon = DiscoveryBeacon(
            agent_id=self.my_agent_id,
            hardware_type=my_capabilities.hardware_type,
            capabilities=[c.name for c in my_capabilities.capabilities],
            pose=my_capabilities.pose,
        )
        return beacon.to_json()

    # ------------------------------------------------------------------
    # Internal loop
    # ------------------------------------------------------------------
    async def _loop(self) -> None:
        while self._running:
            now = time.time()
            for agent_id in list(self._peers.keys()):
                last_seen, _ = self._peers[agent_id]
                if now - last_seen >= self.peer_timeout_sec:
                    self._peers.pop(agent_id, None)
                    if self.on_peer_lost:
                        self.on_peer_lost(agent_id)
            await asyncio.sleep(self.beacon_interval_sec)
