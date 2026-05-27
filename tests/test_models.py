import pytest

from rosclaw_swarm.models import (
    AgentCapabilities,
    Capability,
    SwarmContext,
    Task,
    TaskGraph,
    TaskStatus,
    TaskToken,
)


def test_capability_bounds():
    cap = Capability(name="pick", success_rate=0.92)
    assert cap.name == "pick"
    assert cap.success_rate == 0.92


def test_task_ready():
    t1 = Task(id="t1", description="locate")
    t2 = Task(id="t2", description="navigate", dependencies=["t1"])
    assert t1.is_ready(set())
    assert not t2.is_ready(set())
    assert t2.is_ready({"t1"})


def test_task_graph_ready_tasks():
    t1 = Task(id="t1")
    t2 = Task(id="t2", dependencies=["t1"])
    tg = TaskGraph(graph_id="tg1", goal="test", tasks=[t1, t2])
    ready = tg.ready_tasks()
    assert len(ready) == 1
    assert ready[0].id == "t1"


def test_swarm_context_default_domain():
    ctx = SwarmContext(swarm_session_id="s1")
    assert ctx.dds_domain_id == 42
    assert ctx.shared_world_frame == "swarm_world_001"
