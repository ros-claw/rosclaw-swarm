import pytest

from rosclaw_swarm.models import Task, TaskGraph, TaskStatus, TaskToken
from rosclaw_swarm.planner import TaskPlanner
from rosclaw_swarm.visualizer import to_mermaid, to_dot, to_ascii


def test_to_mermaid_output():
    planner = TaskPlanner()
    graph = planner.plan("Test goal")
    planner.assign_token(graph.tasks[0], "g1")
    mermaid = to_mermaid(graph)
    assert "flowchart TD" in mermaid
    assert "g1" in mermaid
    assert "-->" in mermaid


def test_to_dot_output():
    planner = TaskPlanner()
    graph = planner.plan("Test goal")
    dot = to_dot(graph)
    assert "digraph TaskGraph" in dot
    assert "perception" in dot
    assert "locomotion" in dot


def test_to_ascii_output():
    planner = TaskPlanner()
    graph = planner.plan("Test goal")
    ascii_str = to_ascii(graph)
    assert "TaskGraph:" in ascii_str
    assert "Locate target" in ascii_str


def test_mermaid_with_status_colors():
    planner = TaskPlanner()
    graph = planner.plan("Test goal")
    graph.tasks[0].status = TaskStatus.COMPLETED
    graph.tasks[1].status = TaskStatus.RUNNING
    mermaid = to_mermaid(graph)
    assert "fill:#90EE90" in mermaid  # completed
    assert "fill:#87CEEB" in mermaid  # running
