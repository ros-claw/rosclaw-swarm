"""Swarm Runtime Manager — the macro control plane orchestrator.

Manages swarm session lifecycle: receives high-level intent, discovers
agents, decomposes tasks, schedules assignments, and triggers the DDS
reflex handshake.
"""

from __future__ import annotations

import time
import uuid
from typing import Any, Callable, Dict, List, Optional

from rosclaw_swarm.models import (
    AgentCapabilities,
    SwarmContext,
    Task,
    TaskGraph,
    TaskStatus,
    TaskToken,
)
from rosclaw_swarm.planner import TaskPlanner
from rosclaw_swarm.registry import AgentRegistry, CapabilityRegistry
from rosclaw_swarm.scheduler import SwarmScheduler


class SwarmRuntimeManager:
    """Top-level swarm coordination runtime."""

    def __init__(self) -> None:
        self.agent_registry = AgentRegistry()
        self.capability_registry = CapabilityRegistry()
        self.planner = TaskPlanner()
        self.scheduler = SwarmScheduler(self.agent_registry, self.capability_registry)
        self._sessions: Dict[str, SwarmContext] = {}
        self._event_handlers: Dict[str, List[Callable]] = {}

    # ------------------------------------------------------------------
    # Event bus (minimal pub/sub — can be replaced by rosclaw-event-bus)
    # ------------------------------------------------------------------
    def subscribe(self, event_type: str, handler: Callable) -> None:
        self._event_handlers.setdefault(event_type, []).append(handler)

    def publish(self, event_type: str, payload: Any) -> None:
        for handler in self._event_handlers.get(event_type, []):
            try:
                handler(payload)
            except Exception as e:
                print(f"[SWARM EVENT ERROR] {event_type}: {e}")

    # ------------------------------------------------------------------
    # Session lifecycle
    # ------------------------------------------------------------------
    def create_session(
        self,
        goal: str,
        agent_ids: Optional[List[str]] = None,
        dds_domain_id: int = 42,
    ) -> SwarmContext:
        """Create a new swarm session for a high-level goal."""
        session_id = f"swarm_{int(time.time())}_{uuid.uuid4().hex[:6]}"

        # Discover agents
        if agent_ids:
            topology = [a for a in self.agent_registry.list_all() if a.agent_id in agent_ids]
        else:
            topology = self.agent_registry.list_all()

        # Plan
        task_graph = self.planner.plan(goal)

        ctx = SwarmContext(
            swarm_session_id=session_id,
            topology=topology,
            task_graph=task_graph,
            dds_domain_id=dds_domain_id,
        )
        self._sessions[session_id] = ctx

        self.publish("SwarmSessionCreatedEvent", ctx)
        return ctx

    def schedule_session(self, session_id: str) -> Dict[str, Optional[str]]:
        """Run the scheduler over the session's task graph."""
        ctx = self._sessions.get(session_id)
        if not ctx or not ctx.task_graph:
            return {}

        assignments = self.scheduler.schedule_graph(ctx.task_graph)
        for task_id, agent_id in assignments.items():
            if agent_id:
                task = ctx.task_graph.get_task(task_id)
                if task:
                    self.planner.assign_token(task, agent_id)

        self.publish("SwarmTaskAssignedEvent", {"session_id": session_id, "assignments": assignments})
        return assignments

    def get_session(self, session_id: str) -> Optional[SwarmContext]:
        return self._sessions.get(session_id)

    def list_sessions(self) -> List[SwarmContext]:
        return list(self._sessions.values())

    def activate_reflex(self, session_id: str) -> None:
        """Broadcast SwarmContext to agents, locking them into reflex mode."""
        ctx = self._sessions.get(session_id)
        if not ctx:
            return
        self.publish("SwarmContextActivatedEvent", ctx)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def register_agent(self, agent: AgentCapabilities) -> None:
        self.agent_registry.register(agent)
        for cap in agent.capabilities:
            self.capability_registry.upsert(agent.agent_id, cap)

    def find_capable_agents(self, capability: str) -> List[AgentCapabilities]:
        return self.agent_registry.find(capability)
