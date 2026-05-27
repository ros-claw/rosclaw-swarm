import pytest

from rosclaw_swarm.models import AgentCapabilities, Capability
from rosclaw_swarm.registry import AgentRegistry, CapabilityRegistry


def test_agent_registry_crud():
    reg = AgentRegistry()
    agent = AgentCapabilities(
        agent_id="g1_01",
        hardware_type="G1",
        capabilities=[Capability(name="locomotion", success_rate=0.95)],
    )
    reg.register(agent)
    assert reg.get("g1_01") is not None
    assert reg.get("g1_01").hardware_type == "G1"
    reg.unregister("g1_01")
    assert reg.get("g1_01") is None


def test_agent_registry_find():
    reg = AgentRegistry()
    reg.register(AgentCapabilities(
        agent_id="g1",
        hardware_type="G1",
        capabilities=[Capability(name="locomotion")],
    ))
    reg.register(AgentCapabilities(
        agent_id="ur5",
        hardware_type="UR5e",
        capabilities=[Capability(name="precision_pick")],
    ))
    found = reg.find("locomotion")
    assert len(found) == 1
    assert found[0].agent_id == "g1"


def test_capability_registry_best_agent():
    reg = CapabilityRegistry()
    reg.upsert("g1", Capability(name="pick", success_rate=0.7))
    reg.upsert("ur5", Capability(name="pick", success_rate=0.95))
    best = reg.best_agent("pick")
    assert best == "ur5"


def test_capability_registry_update_success_rate():
    reg = CapabilityRegistry()
    reg.update_success_rate("g1", "pick", 0.8)
    cap = reg.get("g1", "pick")
    assert cap is not None
    assert cap.success_rate == 0.8
