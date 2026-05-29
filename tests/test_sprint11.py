"""Sprint 11 tests — AgentDiscovery, RoleAssigner, TFSync, SafetyZone, DDSGroup, ForceStateShare, CLI."""

import asyncio

import pytest

from rosclaw_swarm import (
    AgentCapabilities,
    AgentDiscovery,
    Capability,
    DDSGroupManager,
    DiscoveryBeacon,
    ForceState,
    ForceStateShare,
    RoleAssigner,
    SafetyZone,
    SafetyZoneManager,
    SwarmRole,
    TFSync,
)
from rosclaw_swarm.models import SwarmContext, TaskGraph


# ------------------------------------------------------------------
# AgentDiscovery
# ------------------------------------------------------------------
def test_discovery_beacon_roundtrip():
    beacon = DiscoveryBeacon(
        agent_id="g1",
        hardware_type="G1",
        capabilities=["locomotion", "manipulation"],
        pose={"x": 1.0, "y": 2.0, "z": 0.0},
    )
    raw = beacon.to_json()
    restored = DiscoveryBeacon.from_json(raw)
    assert restored is not None
    assert restored.agent_id == "g1"
    assert restored.capabilities == ["locomotion", "manipulation"]


def test_discovery_receives_peer():
    disc = AgentDiscovery(my_agent_id="ur5")
    beacon = DiscoveryBeacon(
        agent_id="g1", hardware_type="G1", capabilities=["locomotion"]
    )
    disc.receive_beacon(beacon.to_json())
    peers = disc.list_peers()
    assert len(peers) == 1
    assert peers[0].agent_id == "g1"


def test_discovery_ignores_self():
    disc = AgentDiscovery(my_agent_id="g1")
    beacon = DiscoveryBeacon(
        agent_id="g1", hardware_type="G1", capabilities=["locomotion"]
    )
    disc.receive_beacon(beacon.to_json())
    assert len(disc.list_peers()) == 0


@pytest.mark.asyncio
async def test_discovery_prunes_stale_peers():
    disc = AgentDiscovery(my_agent_id="ur5", peer_timeout_sec=0.1)
    beacon = DiscoveryBeacon(agent_id="g1", hardware_type="G1", capabilities=["locomotion"])
    disc.receive_beacon(beacon.to_json())
    assert len(disc.list_peers()) == 1
    await disc.start()
    await asyncio.sleep(0.2)
    assert len(disc.list_peers()) == 0
    await disc.stop()


# ------------------------------------------------------------------
# RoleAssigner
# ------------------------------------------------------------------
def test_role_assigner_default():
    assigner = RoleAssigner()
    agents = [
        AgentCapabilities(agent_id="g1", hardware_type="G1", capabilities=[Capability(name="spatial_sync")]),
        AgentCapabilities(agent_id="ur5", hardware_type="UR5e", capabilities=[Capability(name="manipulation")]),
    ]
    tg = TaskGraph(graph_id="tg1", goal="lift table")
    roles = assigner.assign(tg, agents)
    assert roles["g1"] == SwarmRole.LEADER
    assert roles["ur5"] == SwarmRole.FOLLOWER


def test_role_assigner_handoff():
    agents = [
        AgentCapabilities(agent_id="g1", hardware_type="G1", capabilities=[Capability(name="locomotion")]),
        AgentCapabilities(agent_id="ur5", hardware_type="UR5e", capabilities=[Capability(name="manipulation")]),
    ]
    tg = TaskGraph(graph_id="tg1", goal="handoff")
    roles = RoleAssigner.handoff_assign(tg, agents)
    assert roles["g1"] == SwarmRole.SUPPLIER
    assert roles["ur5"] == SwarmRole.RECEIVER


# ------------------------------------------------------------------
# TFSync
# ------------------------------------------------------------------
def test_tf_sync_register_and_pose():
    tf = TFSync(session_id="swarm_001")
    tf.register_agent("g1", "g1_base", {"x": 1.0, "y": 0.0, "z": 0.0})
    tf.register_agent("ur5", "ur5_base", {"x": 2.0, "y": 0.0, "z": 0.0})
    rel = tf.get_relative_pose("g1", "ur5")
    assert rel == {"x": 1.0, "y": 0.0, "z": 0.0}


def test_tf_sync_handoff_point():
    tf = TFSync(session_id="swarm_001")
    tf.set_handoff_point("lift", {"x": 1.5, "y": 0.0, "z": 0.5})
    assert tf.get_handoff_point("lift") == {"x": 1.5, "y": 0.0, "z": 0.5}


def test_tf_sync_from_swarm_context():
    ctx = SwarmContext(
        swarm_session_id="swarm_002",
        shared_world_frame="world_42",
        topology=[
            AgentCapabilities(agent_id="g1", hardware_type="G1", pose={"x": 1.0, "y": 0.0, "z": 0.0}),
        ],
    )
    tf = TFSync.from_swarm_context(ctx)
    assert tf.session_id == "swarm_002"
    assert tf.shared_frame == "world_42"
    assert tf.get_agent_pose("g1") == {"x": 1.0, "y": 0.0, "z": 0.0}


# ------------------------------------------------------------------
# SafetyZone
# ------------------------------------------------------------------
def test_safety_zone_overlap():
    z1 = SafetyZone("g1", radius_m=0.5)
    z2 = SafetyZone("ur5", radius_m=0.5)
    pose1 = {"x": 0.0, "y": 0.0, "z": 0.0}
    pose2 = {"x": 0.8, "y": 0.0, "z": 0.0}
    assert z1.check_overlap(z2, pose1, pose2) is True
    pose3 = {"x": 2.0, "y": 0.0, "z": 0.0}
    assert z1.check_overlap(z2, pose1, pose3) is False


def test_safety_zone_manager_conflicts():
    szm = SafetyZoneManager()
    szm.update_zone("g1", SafetyZone("g1", radius_m=0.5))
    szm.update_zone("ur5", SafetyZone("ur5", radius_m=0.5))
    poses = {"g1": {"x": 0.0, "y": 0.0, "z": 0.0}, "ur5": {"x": 0.8, "y": 0.0, "z": 0.0}}
    conflicts = szm.check_all_conflicts(poses)
    assert len(conflicts) == 1
    assert conflicts[0]["agent_1"] == "g1"
    assert conflicts[0]["agent_2"] == "ur5"


# ------------------------------------------------------------------
# DDSGroupManager
# ------------------------------------------------------------------
def test_dds_group_topics():
    dds = DDSGroupManager(session_id="swarm_001", domain_id=42)
    dds.add_agent("g1")
    dds.add_agent("ur5")
    assert dds.reflex_topic("g1") == "/rosclaw/swarm/swarm_001/g1/reflex"
    assert dds.intent_topic() == "/rosclaw/swarm/swarm_001/intent"
    assert dds.safety_topic() == "/rosclaw/swarm/swarm_001/safety"
    assert dds.tf_topic() == "/rosclaw/swarm/swarm_001/tf"
    assert dds.state_topic() == "/rosclaw/swarm/swarm_001/state"


def test_dds_group_dissolve():
    dds = DDSGroupManager(session_id="swarm_001")
    dds.add_agent("g1")
    manifest = dds.dissolve()
    assert manifest["session_id"] == "swarm_001"
    assert len(dds.list_agents()) == 0


# ------------------------------------------------------------------
# ForceStateShare
# ------------------------------------------------------------------
def test_force_state_share_imbalance():
    fss = ForceStateShare()
    fss.update("g1", ForceState("g1", load_ratio=0.3))
    fss.update("ur5", ForceState("ur5", load_ratio=0.7))
    imbalance = fss.compute_load_imbalance()
    assert imbalance["g1"] == pytest.approx(-0.2, abs=0.01)
    assert imbalance["ur5"] == pytest.approx(0.2, abs=0.01)


def test_force_state_share_overload():
    fss = ForceStateShare()
    fss.update("g1", ForceState("g1", load_ratio=0.5))
    fss.update("ur5", ForceState("ur5", load_ratio=0.9))
    overloaded = fss.detect_overload(threshold=0.8)
    assert overloaded == ["ur5"]


# ------------------------------------------------------------------
# CLI
# ------------------------------------------------------------------
def test_cli_discover():
    from rosclaw_swarm.cli import cmd_discover
    import argparse

    args = argparse.Namespace(agents=None)
    ret = cmd_discover(args)
    assert ret == 1  # no agents registered


def test_cli_form_no_agents():
    from rosclaw_swarm.cli import cmd_form
    import argparse

    args = argparse.Namespace(agents=None, task="lift table", robots=None)
    ret = cmd_form(args)
    assert ret == 1  # no agents registered
