import pytest

from rosclaw_swarm.manager import SwarmRuntimeManager
from rosclaw_swarm.models import AgentCapabilities, Capability


def test_end_to_end_session():
    mgr = SwarmRuntimeManager()

    # Register agents
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
    mgr.register_agent(AgentCapabilities(
        agent_id="zed",
        hardware_type="ZED",
        capabilities=[Capability(name="perception", success_rate=0.98)],
        pose={"x": 1.0, "y": 0.0, "z": 1.5},
    ))

    # Create session
    ctx = mgr.create_session("Bring medicine to the elderly")
    assert ctx.swarm_session_id is not None
    assert ctx.task_graph is not None

    # Schedule
    assignments = mgr.schedule_session(ctx.swarm_session_id)
    assert len(assignments) > 0

    # Verify at least one task got assigned
    assigned = [t for t in ctx.task_graph.tasks if t.token is not None]
    assert len(assigned) > 0


def test_event_pub_sub():
    mgr = SwarmRuntimeManager()
    events = []
    mgr.subscribe("SwarmSessionCreatedEvent", lambda payload: events.append("created"))
    mgr.create_session("Test")
    assert "created" in events
