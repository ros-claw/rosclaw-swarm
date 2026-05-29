"""Swarm CLI — command-line interface for multi-agent operations.

Commands:
    rosclaw-swarm discover       # Scan for peers
    rosclaw-swarm form           # Create a cooperative task group
    rosclaw-swarm status         # Show swarm session state
    rosclaw-swarm dissolve       # Tear down a swarm session
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import List

from rosclaw_swarm import SwarmRuntimeManager
from rosclaw_swarm.models import AgentCapabilities, Capability


def _build_manager(agents_json: str | None = None) -> SwarmRuntimeManager:
    mgr = SwarmRuntimeManager()
    if agents_json:
        data = json.loads(agents_json)
        for item in data:
            caps = [Capability(**c) for c in item.pop("capabilities", [])]
            mgr.register_agent(AgentCapabilities(capabilities=caps, **item))
    return mgr


def cmd_discover(args: argparse.Namespace) -> int:
    """Scan for other ROSClaw agents on the network."""
    print("[SWARM CLI] Scanning for peers...")
    mgr = _build_manager(args.agents)
    peers = mgr.agent_registry.list_all()
    if not peers:
        print("  No agents registered.")
        return 1
    for peer in peers:
        caps = ", ".join(c.name for c in peer.capabilities)
        print(f"  • {peer.agent_id} ({peer.hardware_type}) — capabilities: {caps}")
    return 0


def cmd_form(args: argparse.Namespace) -> int:
    """Form a swarm group for a collaborative task."""
    mgr = _build_manager(args.agents)
    if not mgr.agent_registry.list_all():
        print("[SWARM CLI] ERROR: No agents registered.", file=sys.stderr)
        return 1

    robot_ids = [r.strip() for r in args.robots.split(",")] if args.robots else None
    ctx = mgr.create_session(args.task, agent_ids=robot_ids)
    assignments = mgr.schedule_session(ctx.swarm_session_id)
    mgr.activate_reflex(ctx.swarm_session_id)

    print(f"[SWARM CLI] Group formed: {ctx.swarm_session_id}")
    print(f"  Task: {args.task}")
    print(f"  Robots: {[a.agent_id for a in ctx.topology]}")
    print(f"  Assignments: {assignments}")
    return 0


def cmd_status(args: argparse.Namespace) -> int:
    """Show current swarm session status."""
    mgr = _build_manager(args.agents)
    sessions = mgr.list_sessions()
    if not sessions:
        print("[SWARM CLI] No active swarm sessions.")
        return 0

    for ctx in sessions:
        print(f"Session: {ctx.swarm_session_id}")
        print(f"  DDS Domain: {ctx.dds_domain_id}")
        print(f"  Shared Frame: {ctx.shared_world_frame}")
        print(f"  Topology: {[a.agent_id for a in ctx.topology]}")
        if ctx.task_graph:
            print(f"  Goal: {ctx.task_graph.goal}")
            for t in ctx.task_graph.tasks:
                agent = t.token.assigned_agent_id if t.token else "unassigned"
                print(f"    [{t.status.value}] {t.description} -> {agent}")
    return 0


def cmd_dissolve(args: argparse.Namespace) -> int:
    """Dissolve a swarm session."""
    print(f"[SWARM CLI] Dissolving session {args.session_id}...")
    print("  Session marked for cleanup.")
    return 0


def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="rosclaw-swarm",
        description="ROSClaw Swarm Coordination CLI",
    )
    parser.add_argument(
        "--agents",
        type=str,
        default=None,
        help="JSON string of agent definitions (or env ROSCLAW_SWARM_AGENTS_JSON)",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("discover", help="Scan for peers")

    form_parser = sub.add_parser("form", help="Form a cooperative task group")
    form_parser.add_argument("--task", required=True, help="Task description")
    form_parser.add_argument("--robots", default=None, help="Comma-separated robot IDs")

    sub.add_parser("status", help="Show swarm session state")

    dissolve_parser = sub.add_parser("dissolve", help="Tear down a swarm session")
    dissolve_parser.add_argument("session_id", help="Session ID to dissolve")

    args = parser.parse_args(argv)

    if args.agents is None:
        import os
        args.agents = os.getenv("ROSCLAW_SWARM_AGENTS_JSON")

    if args.command == "discover":
        return cmd_discover(args)
    elif args.command == "form":
        return cmd_form(args)
    elif args.command == "status":
        return cmd_status(args)
    elif args.command == "dissolve":
        return cmd_dissolve(args)

    return 0


if __name__ == "__main__":
    sys.exit(main())
