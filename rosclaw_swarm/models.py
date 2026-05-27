"""Core data models for ROSClaw Swarm.

All inter-module communication is typed via Pydantic to enforce contracts
between the macro control plane (1Hz) and the micro reflex plane (1000Hz).
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional, Set

from pydantic import BaseModel, Field


class TaskStatus(str, Enum):
    PENDING = "pending"
    ASSIGNED = "assigned"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class Capability(BaseModel):
    """A single capability entry in the Capability Graph."""

    name: str = Field(..., description="Canonical capability name, e.g. 'precision_pick'")
    skill: Optional[str] = Field(default=None, description="Bound skill identifier")
    success_rate: float = Field(default=0.0, ge=0.0, le=1.0)
    latency_ms: Optional[float] = Field(default=None, description="Typical execution latency")
    metadata: Dict[str, Any] = Field(default_factory=dict)


class AgentCapabilities(BaseModel):
    """Runtime-discoverable capability vector for a single agent."""

    agent_id: str
    hardware_type: str = Field(..., description="e.g. 'G1', 'UR5e', 'ZED'")
    dof: Optional[int] = Field(default=None)
    payload_limit_kg: Optional[float] = Field(default=None)
    capabilities: List[Capability] = Field(default_factory=list)
    active_topics: List[str] = Field(default_factory=list)
    pose: Optional[Dict[str, float]] = Field(default=None, description="Current x, y, z, qw, qx, qy, qz")
    battery_level: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    load: Optional[float] = Field(default=0.0, ge=0.0, le=1.0, description="Current computational load")
    risk_score: float = Field(default=0.0, ge=0.0, le=1.0)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class TaskToken(BaseModel):
    """Runtime token representing an atomic action dispatched to an agent."""

    task_id: str
    action_type: str = Field(..., description="e.g. 'synchronous_lift', 'handoff', 'inspect'")
    target_object_id: Optional[str] = Field(default=None)
    parameters: Dict[str, Any] = Field(default_factory=dict)
    assigned_agent_id: Optional[str] = Field(default=None)


class Task(BaseModel):
    """Node in a Task DAG."""

    id: str
    parent_id: Optional[str] = Field(default=None)
    dependencies: List[str] = Field(default_factory=list)
    skill: Optional[str] = Field(default=None, description="Required skill to execute")
    capability: Optional[str] = Field(default=None, description="Required capability name")
    description: str = Field(default="", description="Human-readable task description")
    token: Optional[TaskToken] = Field(default=None)
    status: TaskStatus = Field(default=TaskStatus.PENDING)
    priority: int = Field(default=5, ge=1, le=10)
    estimated_duration_ms: Optional[int] = Field(default=None)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    def is_ready(self, completed_ids: Set[str]) -> bool:
        """True when all dependencies are satisfied."""
        return all(dep in completed_ids for dep in self.dependencies)


class TaskGraph(BaseModel):
    """Directed Acyclic Graph of decomposed tasks."""

    graph_id: str
    goal: str = Field(..., description="Original high-level intent")
    tasks: List[Task] = Field(default_factory=list)
    root_task_id: Optional[str] = Field(default=None)

    def get_task(self, task_id: str) -> Optional[Task]:
        for t in self.tasks:
            if t.id == task_id:
                return t
        return None

    def ready_tasks(self) -> List[Task]:
        completed = {t.id for t in self.tasks if t.status == TaskStatus.COMPLETED}
        return [t for t in self.tasks if t.status == TaskStatus.PENDING and t.is_ready(completed)]

    def add_task(self, task: Task) -> None:
        self.tasks.append(task)


class SwarmContext(BaseModel):
    """Contract passed from macro control plane to micro reflex plane."""

    swarm_session_id: str
    topology: List[AgentCapabilities] = Field(default_factory=list)
    current_token: Optional[TaskToken] = Field(default=None)
    task_graph: Optional[TaskGraph] = Field(default=None)
    dds_domain_id: int = Field(default=42, description="Physically isolated ROS 2 Domain ID")
    shared_world_frame: str = Field(default="swarm_world_001", description="Unified TF frame")
    metadata: Dict[str, Any] = Field(default_factory=dict)


class SwarmReflexMessage(BaseModel):
    """High-frequency P2P reflex payload (mirrors eventual .msg definition)."""

    stamp_ns: int = Field(..., description="ROS timestamp in nanoseconds")
    sender_agent_id: str
    expected_tf_offsets: List[Dict[str, Any]] = Field(default_factory=list)
    current_tcp_pose: Optional[Dict[str, Any]] = Field(default=None)
    current_tcp_velocity: Optional[Dict[str, Any]] = Field(default=None)
    actual_wrench: Optional[Dict[str, Any]] = Field(default=None)
    joint_torques: List[float] = Field(default_factory=list)
    intent_phase: Optional[str] = Field(default=None, description="e.g. 'approach', 'execute', 'retract'")
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
