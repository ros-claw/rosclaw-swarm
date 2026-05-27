import pytest

from rosclaw_swarm.llm_planner import LLMTaskPlanner, OllamaPlannerBackend
from rosclaw_swarm.planner import TaskPlanner


def test_llm_planner_fallback_without_backend():
    """Without LLM backend, planner should fall back to heuristic rules."""
    planner = LLMTaskPlanner(backend=None)
    planner.register_fallback_rule("lift", TaskPlanner.cooperative_carry)

    graph = planner.plan("G1 and UR5 lift the heavy table together")
    assert len(graph.tasks) == 5
    ids = [t.id for t in graph.tasks]
    assert any("sync" in i for i in ids)
    assert any("lift" in i for i in ids)


def test_llm_planner_default_heuristic():
    """With no backend and no rules, fall back to default 4-step pipeline."""
    planner = LLMTaskPlanner(backend=None)
    graph = planner.plan("Bring medicine")
    assert len(graph.tasks) == 4
    assert graph.tasks[0].capability == "perception"
    assert graph.tasks[1].capability == "locomotion"
    assert graph.tasks[2].capability == "manipulation"
    assert graph.tasks[3].capability == "perception"


def test_ollama_backend_not_running():
    """Ollama backend gracefully fails when server is offline."""
    backend = OllamaPlannerBackend(base_url="http://localhost:59999")
    result = backend.decompose("test goal")
    assert result is None
