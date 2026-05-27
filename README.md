# ROSClaw-Swarm

[![CI](https://github.com/ros-claw/rosclaw-swarm/actions/workflows/ci.yml/badge.svg)](https://github.com/ros-claw/rosclaw-swarm/actions)
**The Swarm Coordination Runtime for Physical Intelligence**

> Collaboration Grounding — stripping away high-latency LLM text chatter and
> establishing <5ms native P2P physical reflex links between heterogeneous robots.

---

## Philosophy

ROSClaw-Swarm is **not** just another multi-robot framework. It is the **Society Layer** of Physical Intelligence:

```text
Individual Intelligence  →  Collective Intelligence
     Agent                     Swarm
     Memory                    Collective Memory
     Skill                     Team Skill
```

Single Agent solves Symbol Grounding.  
Swarm solves Collective Grounding.

---

## Architecture

### Dual-Plane Design

```text
[ Agent Runtime / LLM ]  (1 Hz  low-frequency intent )
           ↓
+-------------------------------------------+
| Macro Control Plane                       |  Task planning, role assignment, discovery
+-------------------------------------------+
           ↓ (SwarmContext contract)
+-------------------------------------------+
| Micro Physical Reflex Plane               |  DDS P2P reflex handshake, force sync
|                    <5ms                   |
+-------------------------------------------+
           ↓
   [ Robot A ] ←——(DDS)——→ [ Robot B ]
```

### Five Subsystems

| Subsystem | Responsibility | Analogy |
|-----------|----------------|---------|
| **planner** | Task decomposition into DAG | Compiler |
| **scheduler** | Capability-aware agent selection | Kubernetes Scheduler |
| **discovery** | Agent & capability registration | K8s Service Discovery |
| **coordination** | DDS Reflex Handshake, TF sync | Nervous system |
| **evolution** | Collective memory & skill diffusion | Darwin Arena |

---

## Quick Start

```bash
pip install -e ".[dev]"
pytest tests/
```

### Register agents and plan a mission

```python
from rosclaw_swarm import SwarmRuntimeManager
from rosclaw_swarm.models import AgentCapabilities, Capability

mgr = SwarmRuntimeManager()

mgr.register_agent(AgentCapabilities(
    agent_id="g1",
    hardware_type="G1",
    capabilities=[Capability(name="locomotion", success_rate=0.95)],
    pose={"x": 0.0, "y": 0.0, "z": 0.0},
))

mgr.register_agent(AgentCapabilities(
    agent_id="ur5",
    hardware_type="UR5e",
    capabilities=[Capability(name="manipulation", success_rate=0.92)],
    pose={"x": 2.0, "y": 0.0, "z": 0.0},
))

ctx = mgr.create_session("Bring medicine to the elderly")
assignments = mgr.schedule_session(ctx.swarm_session_id)
mgr.activate_reflex(ctx.swarm_session_id)

print(assignments)
```

---

## Module Structure

```text
rosclaw_swarm/
├── models.py        # Pydantic contracts: SwarmContext, Task, Capability, ReflexMessage
├── registry.py      # AgentRegistry + CapabilityRegistry (discovery layer)
├── planner.py       # TaskPlanner — DAG decomposition
├── scheduler.py     # SwarmScheduler — multi-factor scoring
├── manager.py       # SwarmRuntimeManager — session lifecycle
├── dds_bridge.py    # QoS profiles & topic naming
├── reflex.py        # ReflexHandshake state machine
└── mcp_tools.py     # MCP tools exposed to Claude/LLM
```

---

## Position in ROSClaw Ecosystem

```text
Physical World
      ↓
Practice  →  Memory  →  SeekDB
                            ↓
                    Capability Graph
                            ↓
                    ROSClaw-Swarm  ←  You are here
                            ↓
         ┌────────┬─────────┬────────┐
         ↓        ↓         ↓        ↓
      Planner  Scheduler  Discovery  Coordination
                                    ↓
                            Agent Runtime
                                    ↓
                    G1 / UR5 / Drone / Camera
```

---

## License

MIT

---

## MCP Server

ROSClaw-Swarm exposes a **FastMCP** server so Claude (or any LLM) can orchestrate physical swarm tasks directly.

### Install with MCP support

```bash
pip install -e ".[mcp]"
```

### Start the server

**Stdio mode** (for Claude Desktop):
```bash
rosclaw-swarm-server
# or
python -m rosclaw_swarm.server
```

**SSE mode** (for remote clients):
```bash
rosclaw-swarm-server --transport sse --port 8000
```

### Pre-load agents from JSON

```bash
rosclaw-swarm-server --agents agents_example.json
```

Or via environment variable:
```bash
export ROSCLAW_SWARM_AGENTS_JSON='[{"agent_id":"g1","hardware_type":"G1",...}]'
rosclaw-swarm-server
```

### MCP Tools exposed

| Tool | Purpose |
|------|---------|
| `create_swarm_session` | Create a swarm session from a high-level goal |
| `find_capable_agents` | Discover agents by capability |
| `establish_swarm_handoff` | Set up physical handoff between two agents |
| `get_session_status` | Query current session status |

### Claude Desktop configuration

Add to your Claude Desktop config (`~/.config/claude/claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "rosclaw-swarm": {
      "command": "rosclaw-swarm-server",
      "env": {
        "PYTHONPATH": "/path/to/rosclaw_swarm"
      }
    }
  }
}
```
