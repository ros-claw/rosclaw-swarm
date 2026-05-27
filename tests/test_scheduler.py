import pytest

from rosclaw_swarm.models import AgentCapabilities, Capability, Task
from rosclaw_swarm.planner import TaskPlanner
from rosclaw_swarm.registry import AgentRegistry, CapabilityRegistry
from rosclaw_swarm.scheduler import SwarmScheduler


def test_scheduler_selects_best_by_success_rate():
    agents = AgentRegistry()
    caps = CapabilityRegistry()

    agents.register(AgentCapabilities(
        agent_id="g1",
        hardware_type="G1",
        capabilities=[Capability(name="pick", success_rate=0.6)],
    ))
    agents.register(AgentCapabilities(
        agent_id="ur5",
        hardware_type="UR5e",
        capabilities=[Capability(name="pick", success_rate=0.95)],
    ))
    caps.upsert("g1", Capability(name="pick", success_rate=0.6))
    caps.upsert("ur5", Capability(name="pick", success_rate=0.95))

    scheduler = SwarmScheduler(agents, caps)
    task = Task(id="t1", capability="pick")
    best = scheduler.select_best_agent(task)
    assert best == "ur5"


def test_scheduler_penalises_low_battery():
    agents = AgentRegistry()
    caps = CapabilityRegistry()

    agents.register(AgentCapabilities(
        agent_id="g1",
        hardware_type="G1",
        capabilities=[Capability(name="pick")],
        battery_level=0.1,
        risk_score=0.0,
    ))
    agents.register(AgentCapabilities(
        agent_id="ur5",
        hardware_type="UR5e",
        capabilities=[Capability(name="pick")],
        battery_level=0.9,
        risk_score=0.0,
    ))
    caps.upsert("g1", Capability(name="pick", success_rate=0.95))
    caps.upsert("ur5", Capability(name="pick", success_rate=0.95))

    scheduler = SwarmScheduler(agents, caps)
    task = Task(id="t1", capability="pick")
    best = scheduler.select_best_agent(task)
    assert best == "ur5"


def test_scheduler_uses_proximity():
    agents = AgentRegistry()
    caps = CapabilityRegistry()

    agents.register(AgentCapabilities(
        agent_id="far",
        hardware_type="G1",
        capabilities=[Capability(name="pick")],
        pose={"x": 100.0, "y": 0, "z": 0},
    ))
    agents.register(AgentCapabilities(
        agent_id="near",
        hardware_type="G1",
        capabilities=[Capability(name="pick")],
        pose={"x": 1.0, "y": 0, "z": 0},
    ))
    caps.upsert("far", Capability(name="pick", success_rate=0.9))
    caps.upsert("near", Capability(name="pick", success_rate=0.9))

    scheduler = SwarmScheduler(agents, caps)
    task = Task(id="t1", capability="pick")
    best = scheduler.select_best_agent(task, task_location=(0.0, 0.0, 0.0))
    assert best == "near"


def test_schedule_graph():
    agents = AgentRegistry()
    caps = CapabilityRegistry()
    agents.register(AgentCapabilities(
        agent_id="g1",
        hardware_type="G1",
        capabilities=[Capability(name="perception")],
    ))
    caps.upsert("g1", Capability(name="perception", success_rate=0.9))

    planner = TaskPlanner()
    graph = planner.plan("Test")
    scheduler = SwarmScheduler(agents, caps)
    assignments = scheduler.schedule_graph(graph)
    assert len(assignments) >= 1
