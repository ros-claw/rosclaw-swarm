import asyncio
import pytest

from rosclaw_swarm.models import Task, TaskStatus
from rosclaw_swarm.simulation import SwarmSimulator, SimulatedAgent


def test_simulated_agent_pose_update():
    agent = SimulatedAgent(agent_id="g1", hardware_type="G1")
    agent.velocity = {"x": 1.0, "y": 0.0, "z": 0.0}
    agent.update_pose(dt=1.0)
    assert agent.pose["x"] > 0.0


@pytest.mark.asyncio
async def test_simulator_task_dispatch():
    sim = SwarmSimulator()
    sim.add_agent(SimulatedAgent(agent_id="g1", hardware_type="G1", success_rate=1.0))

    completed = []
    sim.on("task_complete", lambda tid, ok: completed.append((tid, ok)))

    task = Task(id="t1", capability="locomotion", description="move")
    await sim.dispatch_task(task, "g1")
    await asyncio.sleep(1.5)  # let task finish

    assert len(completed) == 1
    assert completed[0][0] == "t1"
    assert completed[0][1] is True
    assert task.status == TaskStatus.COMPLETED


@pytest.mark.asyncio
async def test_simulator_run_loop():
    sim = SwarmSimulator()
    sim.add_agent(SimulatedAgent(agent_id="g1", hardware_type="G1"))
    sim.set_agent_velocity("g1", 0.5, 0.0)

    ticks = []
    sim.on("tick", lambda s: ticks.append(1))

    await sim.run(duration_seconds=0.3)
    assert len(ticks) >= 2
    assert sim.agents["g1"].pose["x"] > 0.0


def test_simulator_reflex_message():
    sim = SwarmSimulator()
    sim.add_agent(SimulatedAgent(agent_id="g1", hardware_type="G1"))
    msg = sim.generate_reflex_message("g1")
    assert msg.sender_agent_id == "g1"
    assert msg.confidence > 0.0
    assert len(msg.joint_torques) == 6


def test_simulator_state_snapshot():
    sim = SwarmSimulator()
    sim.add_agent(SimulatedAgent(agent_id="g1", hardware_type="G1", battery_level=0.75))
    state = sim.get_state()
    assert "g1" in state
    assert state["g1"]["battery"] == 0.75
