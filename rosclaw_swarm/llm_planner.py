"""LLM-based Task Planner — decomposes goals via Claude API or local LLM.

No ROS required.  Falls back to heuristic rules if the LLM is unavailable.
"""

from __future__ import annotations

import json
import os
from typing import Callable, Dict, List, Optional

from rosclaw_swarm.models import Task, TaskGraph


_DECOMPOSE_PROMPT = """You are a task planner for a multi-robot swarm.
Decompose the user's high-level goal into a directed acyclic graph (DAG) of atomic tasks.

Each task must have:
- id: unique string
- description: what to do
- capability: required robot capability (e.g. "perception", "locomotion", "manipulation", "synchronous_lift", "spatial_sync")
- dependencies: list of task ids that must complete first
- priority: 1-10 (higher = more urgent)

Respond ONLY with valid JSON in this exact format:
{
  "tasks": [
    {"id": "t1", "description": "...", "capability": "...", "dependencies": [], "priority": 5},
    {"id": "t2", "description": "...", "capability": "...", "dependencies": ["t1"], "priority": 5}
  ]
}

Examples:

Goal: "G1 and UR5 lift the heavy table together"
{
  "tasks": [
    {"id": "sync", "description": "Synchronise spatial frames", "capability": "spatial_sync", "dependencies": [], "priority": 10},
    {"id": "approach", "description": "Approach lift points", "capability": "locomotion", "dependencies": ["sync"], "priority": 9},
    {"id": "lift", "description": "Synchronous lift", "capability": "synchronous_lift", "dependencies": ["approach"], "priority": 10},
    {"id": "transport", "description": "Transport to destination", "capability": "locomotion", "dependencies": ["lift"], "priority": 8},
    {"id": "place", "description": "Place and release", "capability": "synchronous_lift", "dependencies": ["transport"], "priority": 9}
  ]
}

Goal: "{goal}"
"""


class LLMPlannerBackend:
    """Abstract backend for LLM-based planning."""

    def decompose(self, goal: str) -> Optional[Dict]:
        raise NotImplementedError


class ClaudePlannerBackend(LLMPlannerBackend):
    """Uses Anthropic Claude API for task decomposition."""

    def __init__(self, model: str = "claude-sonnet-4-6", api_key: Optional[str] = None) -> None:
        self.model = model
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        self._client = None

    def _get_client(self):
        if self._client is None:
            try:
                import anthropic
            except ImportError as e:
                raise RuntimeError("anthropic package required. pip install anthropic") from e
            if not self.api_key:
                raise RuntimeError("ANTHROPIC_API_KEY not set")
            self._client = anthropic.Anthropic(api_key=self.api_key)
        return self._client

    def decompose(self, goal: str) -> Optional[Dict]:
        try:
            client = self._get_client()
            response = client.messages.create(
                model=self.model,
                max_tokens=2048,
                temperature=0.2,
                system="You are a precise task planner for physical robot swarms. Output only valid JSON.",
                messages=[{"role": "user", "content": _DECOMPOSE_PROMPT.format(goal=goal)}],
            )
            text = response.content[0].text if response.content else ""
            if "```json" in text:
                text = text.split("```json")[1].split("```")[0]
            elif "```" in text:
                text = text.split("```")[1].split("```")[0]
            return json.loads(text.strip())
        except Exception as e:
            print(f"[LLM Planner] Claude decomposition failed: {e}")
            return None


class OllamaPlannerBackend(LLMPlannerBackend):
    """Uses local Ollama instance — no API key, no cloud, fully offline."""

    def __init__(self, model: str = "qwen2.5:14b", base_url: str = "http://localhost:11434") -> None:
        self.model = model
        self.base_url = base_url.rstrip("/")

    def decompose(self, goal: str) -> Optional[Dict]:
        try:
            import urllib.request
            req = urllib.request.Request(
                f"{self.base_url}/api/generate",
                data=json.dumps({
                    "model": self.model,
                    "prompt": _DECOMPOSE_PROMPT.format(goal=goal),
                    "stream": False,
                    "format": "json",
                }).encode(),
                headers={"Content-Type": "application/json"},
            )
            with urllib.request.urlopen(req, timeout=60) as resp:
                data = json.loads(resp.read())
            text = data.get("response", "")
            return json.loads(text.strip())
        except Exception as e:
            print(f"[LLM Planner] Ollama decomposition failed: {e}")
            return None


class LLMTaskPlanner:
    """Planner that uses an LLM backend, with heuristic fallback."""

    def __init__(self, backend: Optional[LLMPlannerBackend] = None) -> None:
        self.backend = backend
        self._fallback_rules: Dict[str, Callable] = {}

    def register_fallback_rule(self, goal_pattern: str, rule_fn: Callable) -> None:
        self._fallback_rules[goal_pattern] = rule_fn

    def plan(self, goal: str, graph_id: Optional[str] = None) -> TaskGraph:
        import time, uuid
        gid = graph_id or f"tg_{int(time.time())}_{uuid.uuid4().hex[:6]}"

        if self.backend:
            result = self.backend.decompose(goal)
            if result and "tasks" in result:
                tasks = []
                for item in result["tasks"]:
                    tasks.append(Task(
                        id=item.get("id", f"{gid}_t"),
                        description=item.get("description", ""),
                        capability=item.get("capability"),
                        dependencies=item.get("dependencies", []),
                        priority=item.get("priority", 5),
                    ))
                return TaskGraph(
                    graph_id=gid, goal=goal, tasks=tasks,
                    root_task_id=tasks[0].id if tasks else None,
                )

        for pattern, rule_fn in self._fallback_rules.items():
            if pattern.lower() in goal.lower():
                return rule_fn(goal, gid)

        return self._default_decompose(goal, gid)

    def _default_decompose(self, goal: str, graph_id: str) -> TaskGraph:
        base = f"t_{graph_id}"
        t_locate = Task(id=f"{base}_locate", description=f"Locate target for: {goal}", capability="perception", priority=5)
        t_navigate = Task(id=f"{base}_navigate", description=f"Navigate to target for: {goal}", capability="locomotion", dependencies=[t_locate.id], priority=5)
        t_manipulate = Task(id=f"{base}_manipulate", description=f"Manipulate target for: {goal}", capability="manipulation", dependencies=[t_navigate.id], priority=5)
        t_verify = Task(id=f"{base}_verify", description=f"Verify outcome for: {goal}", capability="perception", dependencies=[t_manipulate.id], priority=3)
        return TaskGraph(graph_id=graph_id, goal=goal, tasks=[t_locate, t_navigate, t_manipulate, t_verify], root_task_id=t_locate.id)
