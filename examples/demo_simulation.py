"""Pure-software end-to-end demo — no ROS, no hardware, no API keys.

Shows the full Swarm lifecycle:
1. Register virtual agents
2. Create swarm session from natural language goal
3. Plan task DAG (cooperative carry)
4. Multi-round scheduling as dependencies resolve
5. Simulate execution in virtual physics
6. Visualize results
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from rosclaw_swarm import SwarmRuntimeManager, SwarmSimulator, SimulatedAgent, to_mermaid, to_ascii
from rosclaw_swarm.models import AgentCapabilities, Capability


async def main():
    print("=" * 60)
    print("ROSClaw-Swarm Pure-Software Demo")
    print("No ROS. No hardware. Just Python.")
    print("=" * 60)

    sim = SwarmSimulator()
    sim.add_agent(SimulatedAgent(agent_id="g1", hardware_type="G1", pose={"x": 0.0, "y": 0.0, "z": 0.0}, battery_level=0.85, success_rate=0.95))
    sim.add_agent(SimulatedAgent(agent_id="ur5", hardware_type="UR5e", pose={"x": 2.0, "y": 0.0, "z": 0.0}, battery_level=0.90, success_rate=0.92))
    sim.add_agent(SimulatedAgent(agent_id="zed", hardware_type="ZED", pose={"x": 1.0, "y": 0.0, "z": 1.5}, battery_level=0.70, success_rate=0.98))

    mgr = SwarmRuntimeManager()
    capability_map = {
        "G1": [
            Capability(name="locomotion", success_rate=0.95),
            Capability(name="manipulation", success_rate=0.80),
            Capability(name="synchronous_lift", success_rate=0.85),
        ],
        "UR5e": [
            Capability(name="precision_pick", success_rate=0.92),
            Capability(name="manipulation", success_rate=0.95),
            Capability(name="synchronous_lift", success_rate=0.90),
        ],
        "ZED": [
            Capability(name="perception", success_rate=0.98),
            Capability(name="spatial_sync", success_rate=0.95),
        ],
    }
    for sim_agent in sim.agents.values():
        caps = capability_map.get(sim_agent.hardware_type, [])
        mgr.register_agent(AgentCapabilities(
            agent_id=sim_agent.agent_id, hardware_type=sim_agent.hardware_type,
            capabilities=caps, pose=sim_agent.pose,
            battery_level=sim_agent.battery_level, load=sim_agent.load,
        ))

    goal = "G1 and UR5 lift the heavy table together"
    ctx = mgr.create_session(goal)
    print(f"\nGoal: {ctx.task_graph.goal}")
    print(f"Planned {len(ctx.task_graph.tasks)} tasks:")
    for t in ctx.task_graph.tasks:
        print(f"   - {t.description} ({t.capability})")

    completed_tasks = []
    sim.on("task_complete", lambda tid, ok: completed_tasks.append((tid, ok)))

    round_num = 0
    while True:
        ready = ctx.task_graph.ready_tasks()
        if not ready:
            break
        round_num += 1
        print(f"\nScheduling Round {round_num}")
        assignments = mgr.schedule_session(ctx.swarm_session_id)
        for task_id, agent_id in assignments.items():
            task = ctx.task_graph.get_task(task_id)
            print(f"   -> {task.description} -> {agent_id}")
            await sim.dispatch_task(task, agent_id)
        await asyncio.sleep(1.5)

    print(f"\nCompleted {len(completed_tasks)}/{len(ctx.task_graph.tasks)} tasks")
    for tid, ok in completed_tasks:
        task = ctx.task_graph.get_task(tid)
        agent = task.token.assigned_agent_id if task.token else "?"
        print(f"   [{'OK' if ok else 'FAIL'}] [{agent}] {task.description}")

    print("\n--- ASCII Tree ---")
    print(to_ascii(ctx.task_graph))

    print("\n--- Mermaid Flowchart ---")
    print(to_mermaid(ctx.task_graph))

    print("\n--- Final Agent States ---")
    for aid, state in sim.get_state().items():
        p = state['pose']
        print(f"   {aid}: pos=({p['x']:.2f}, {p['y']:.2f}), battery={state['battery']:.2f}")


if __name__ == "__main__":
    asyncio.run(main())
