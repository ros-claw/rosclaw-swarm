"""Pure-software simulation mode — no ROS, no hardware required.

Runs the entire Swarm stack in a virtual physics sandbox so you can:
- Test task planning and scheduling without robots
- Validate MCP tool workflows in CI
- Demo the system on a laptop
"""

from __future__ import annotations

import asyncio
import random
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional

from rosclaw_swarm.models import (
    AgentCapabilities,
    SwarmContext,
    SwarmReflexMessage,
    Task,
    TaskStatus,
)


@dataclass
class SimulatedAgent:
    """A software-only agent that mimics physical robot behavior."""

    agent_id: str
    hardware_type: str
    pose: Dict[str, float] = field(default_factory=lambda: {"x": 0.0, "y": 0.0, "z": 0.0})
    velocity: Dict[str, float] = field(default_factory=lambda: {"x": 0.0, "y": 0.0, "z": 0.0})
    battery_level: float = 1.0
    load: float = 0.0
    force_sensor: float = 0.0
    is_busy: bool = False
    current_task: Optional[str] = None

    # Simulation parameters
    move_speed: float = 0.5  # m/s
    success_rate: float = 0.9
    noise_factor: float = 0.05

    async def execute_task(self, task: Task, on_complete: Callable[[str, bool], None]) -> None:
        """Simulate task execution with realistic timing and occasional failure."""
        self.is_busy = True
        self.current_task = task.id
        task.status = TaskStatus.RUNNING

        # Simulate work duration based on capability complexity
        duration = random.uniform(0.5, 2.0)
        if task.capability in {"synchronous_lift", "spatial_sync"}:
            duration = random.uniform(1.0, 3.0)

        steps = max(1, int(duration * 3))
        for _ in range(steps):
            await asyncio.sleep(0.1)
            self.battery_level = max(0.0, self.battery_level - 0.001)
            self.load = min(1.0, self.load + random.uniform(-0.05, 0.05))

        # Determine success/failure
        success = random.random() < self.success_rate
        if task.capability == "manipulation":
            success = random.random() < (self.success_rate - 0.05)

        task.status = TaskStatus.COMPLETED if success else TaskStatus.FAILED
        self.is_busy = False
        self.current_task = None
        on_complete(task.id, success)

    def update_pose(self, dt: float = 0.1) -> None:
        """Apply velocity to position (Euler integration)."""
        for axis in ("x", "y", "z"):
            self.pose[axis] += self.velocity[axis] * dt + random.uniform(-self.noise_factor, self.noise_factor) * dt

    def read_force_sensor(self) -> float:
        """Simulate force sensor with noise."""
        return self.force_sensor + random.uniform(-0.1, 0.1)


class SwarmSimulator:
    """Virtual swarm environment — replaces ROS 2 + real robots."""

    def __init__(self) -> None:
        self.agents: Dict[str, SimulatedAgent] = {}
        self._running = False
        self._tick_rate_hz = 10.0
        self._callbacks: Dict[str, List[Callable]] = {
            "task_complete": [],
            "collision": [],
            "tick": [],
        }
        self._task_queue: List[Task] = []

    def add_agent(self, agent: SimulatedAgent) -> None:
        self.agents[agent.agent_id] = agent

    def on(self, event: str, callback: Callable) -> None:
        self._callbacks.setdefault(event, []).append(callback)

    def _emit(self, event: str, *args: Any) -> None:
        for cb in self._callbacks.get(event, []):
            try:
                cb(*args)
            except Exception as e:
                print(f"[SIM ERROR] {event}: {e}")

    async def run(self, duration_seconds: Optional[float] = None) -> None:
        """Run the simulation loop."""
        self._running = True
        start = time.monotonic()
        dt = 1.0 / self._tick_rate_hz

        while self._running:
            if duration_seconds and (time.monotonic() - start) >= duration_seconds:
                break

            for agent in self.agents.values():
                agent.update_pose(dt)

            self._emit("tick", self)
            await asyncio.sleep(dt)

    def stop(self) -> None:
        self._running = False

    async def dispatch_task(self, task: Task, agent_id: str) -> None:
        """Dispatch a task to a simulated agent."""
        agent = self.agents.get(agent_id)
        if not agent:
            task.status = TaskStatus.FAILED
            self._emit("task_complete", task.id, False)
            return

        def on_done(task_id: str, success: bool) -> None:
            self._emit("task_complete", task_id, success)

        asyncio.create_task(agent.execute_task(task, on_done))

    def generate_reflex_message(self, agent_id: str) -> SwarmReflexMessage:
        """Generate a synthetic reflex message for testing."""
        agent = self.agents[agent_id]
        return SwarmReflexMessage(
            stamp_ns=int(time.time() * 1e9),
            sender_agent_id=agent_id,
            current_tcp_pose=agent.pose.copy(),
            current_tcp_velocity=agent.velocity.copy(),
            actual_wrench={"force": {"x": agent.force_sensor, "y": 0.0, "z": 0.0}},
            joint_torques=[random.uniform(-0.5, 0.5) for _ in range(6)],
            confidence=random.uniform(0.85, 1.0),
        )

    def set_agent_velocity(self, agent_id: str, vx: float, vy: float, vz: float = 0.0) -> None:
        if agent_id in self.agents:
            self.agents[agent_id].velocity = {"x": vx, "y": vy, "z": vz}

    def get_state(self) -> Dict[str, Any]:
        """Snapshot of the entire simulation state."""
        return {
            agent_id: {
                "pose": a.pose,
                "battery": a.battery_level,
                "load": a.load,
                "busy": a.is_busy,
                "task": a.current_task,
            }
            for agent_id, a in self.agents.items()
        }
