import pytest

from rosclaw_swarm.models import TaskStatus
from rosclaw_swarm.planner import TaskPlanner


def test_default_plan_structure():
    planner = TaskPlanner()
    graph = planner.plan("Bring medicine to the elderly")
    assert graph.goal == "Bring medicine to the elderly"
    assert len(graph.tasks) == 4
    ids = [t.id for t in graph.tasks]
    assert any("locate" in i for i in ids)
    assert any("navigate" in i for i in ids)
    assert any("manipulate" in i for i in ids)
    assert any("verify" in i for i in ids)


def test_cooperative_carry_rule():
    planner = TaskPlanner()
    planner.register_rule("lift", TaskPlanner.cooperative_carry)
    graph = planner.plan("G1 and UR5 lift the heavy table together")
    assert len(graph.tasks) == 5
    ids = [t.id for t in graph.tasks]
    assert any("sync" in i for i in ids)
    assert any("lift" in i for i in ids)


def test_assign_token():
    planner = TaskPlanner()
    graph = planner.plan("Test goal")
    task = graph.tasks[0]
    planner.assign_token(task, "g1_01")
    assert task.status == TaskStatus.ASSIGNED
    assert task.token is not None
    assert task.token.assigned_agent_id == "g1_01"
