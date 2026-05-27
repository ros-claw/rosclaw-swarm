"""ROSClaw Swarm Coordination Runtime — Collaboration Grounding for Physical Intelligence.

Provides the Society Layer that elevates individual Agent intelligence into
Collective Intelligence through task planning, capability-aware scheduling,
agent discovery, and low-latency physical coordination.

Works with or without ROS 2 — use Simulation mode for pure-software testing.
"""

__version__ = "0.1.0"

from rosclaw_swarm.models import (
    AgentCapabilities,
    Capability,
    SwarmContext,
    Task,
    TaskGraph,
    TaskToken,
    TaskStatus,
    SwarmReflexMessage,
)
from rosclaw_swarm.registry import AgentRegistry, CapabilityRegistry
from rosclaw_swarm.planner import TaskPlanner
from rosclaw_swarm.scheduler import SwarmScheduler
from rosclaw_swarm.manager import SwarmRuntimeManager
from rosclaw_swarm.mcp_tools import SwarmMCPServer
from rosclaw_swarm.llm_planner import (
    LLMTaskPlanner,
    ClaudePlannerBackend,
    OllamaPlannerBackend,
)
from rosclaw_swarm.visualizer import to_mermaid, to_dot, to_ascii
from rosclaw_swarm.simulation import SwarmSimulator, SimulatedAgent

__all__ = [
    "AgentCapabilities",
    "Capability",
    "SwarmContext",
    "Task",
    "TaskGraph",
    "TaskToken",
    "TaskStatus",
    "SwarmReflexMessage",
    "AgentRegistry",
    "CapabilityRegistry",
    "TaskPlanner",
    "SwarmScheduler",
    "SwarmRuntimeManager",
    "SwarmMCPServer",
    "LLMTaskPlanner",
    "ClaudePlannerBackend",
    "OllamaPlannerBackend",
    "to_mermaid",
    "to_dot",
    "to_ascii",
    "SwarmSimulator",
    "SimulatedAgent",
]
