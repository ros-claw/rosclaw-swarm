"""Task Planner — decomposes high-level intent into a Task DAG.

Macro control plane (1Hz).  Receives semantic goals from the Agent Runtime
and expands them into atomic, dependency-ordered tasks.
"""

from __future__ import annotations

import time
import uuid
from typing import Dict, List, Optional

from rosclaw_swarm.models import Task, TaskGraph, TaskStatus, TaskToken


class TaskPlanner:
    """Decomposes a high-level goal into a directed acyclic graph of Tasks."""

    def __init__(self) -> None:
        self._decomposition_rules: Dict[str, callable] = {}

    def register_rule(self, goal_pattern: str, rule_fn: callable) -> None:
        """Register a custom decomposition rule for a goal pattern."""
        self._decomposition_rules[goal_pattern] = rule_fn

    def plan(self, goal: str, graph_id: Optional[str] = None) -> TaskGraph:
        """Convert a natural-language goal into a TaskGraph.

        For now, if a registered rule matches we use it; otherwise we fall
        back to a default heuristic decomposition.  Future iterations will
        integrate an LLM-based planner.
        """
        gid = graph_id or f"tg_{int(time.time())}_{uuid.uuid4().hex[:6]}"

        for pattern, rule_fn in self._decomposition_rules.items():
            if pattern.lower() in goal.lower():
                return rule_fn(goal, gid)

        return self._default_decompose(goal, gid)

    def _default_decompose(self, goal: str, graph_id: str) -> TaskGraph:
        """Heuristic fallback: produce a simple linear pipeline.

        locate → navigate → manipulate → verify
        """
        base = f"t_{graph_id}"
        tasks: List[Task] = []

        t_locate = Task(
            id=f"{base}_locate",
            description=f"Locate target for: {goal}",
            capability="perception",
            priority=5,
        )
        tasks.append(t_locate)

        t_navigate = Task(
            id=f"{base}_navigate",
            description=f"Navigate to target for: {goal}",
            capability="locomotion",
            dependencies=[t_locate.id],
            priority=5,
        )
        tasks.append(t_navigate)

        t_manipulate = Task(
            id=f"{base}_manipulate",
            description=f"Manipulate target for: {goal}",
            capability="manipulation",
            dependencies=[t_navigate.id],
            priority=5,
        )
        tasks.append(t_manipulate)

        t_verify = Task(
            id=f"{base}_verify",
            description=f"Verify outcome for: {goal}",
            capability="perception",
            dependencies=[t_manipulate.id],
            priority=3,
        )
        tasks.append(t_verify)

        return TaskGraph(
            graph_id=graph_id,
            goal=goal,
            tasks=tasks,
            root_task_id=t_locate.id,
        )

    @staticmethod
    def cooperative_carry(goal: str, graph_id: str) -> TaskGraph:
        """Built-in rule: two-agent cooperative carry.

        Example goal: "G1 and UR5 lift the heavy table together"
        """
        base = f"t_{graph_id}"

        t_sync = Task(
            id=f"{base}_sync",
            description="Synchronise spatial frames and handshake",
            capability="spatial_sync",
            priority=10,
        )
        t_approach = Task(
            id=f"{base}_approach",
            description="Both agents approach lift points",
            capability="locomotion",
            dependencies=[t_sync.id],
            priority=9,
        )
        t_lift = Task(
            id=f"{base}_lift",
            description="Synchronous lift via DDS reflex",
            capability="synchronous_lift",
            dependencies=[t_approach.id],
            priority=10,
        )
        t_transport = Task(
            id=f"{base}_transport",
            description="Transport object to destination",
            capability="locomotion",
            dependencies=[t_lift.id],
            priority=8,
        )
        t_place = Task(
            id=f"{base}_place",
            description="Synchronous place / release",
            capability="synchronous_lift",
            dependencies=[t_transport.id],
            priority=9,
        )

        return TaskGraph(
            graph_id=graph_id,
            goal=goal,
            tasks=[t_sync, t_approach, t_lift, t_transport, t_place],
            root_task_id=t_sync.id,
        )

    def assign_token(self, task: Task, agent_id: str, action_type: str = "execute") -> Task:
        """Bind a task to a concrete agent and produce a runtime token."""
        task.token = TaskToken(
            task_id=task.id,
            action_type=action_type,
            assigned_agent_id=agent_id,
        )
        task.status = TaskStatus.ASSIGNED
        return task
