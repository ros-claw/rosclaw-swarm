# ROSClaw-Swarm

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
