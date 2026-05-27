"""MCP Server entry point for ROSClaw-Swarm.

Starts a FastMCP server exposing swarm orchestration tools to Claude / LLM.

Usage:
    python -m rosclaw_swarm.server
    rosclaw-swarm-server          # after pip install
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
from typing import Any, Dict, List

from rosclaw_swarm import SwarmRuntimeManager, SwarmMCPServer
from rosclaw_swarm.models import AgentCapabilities, Capability


def load_agents_from_env() -> List[AgentCapabilities]:
    """Load agent definitions from ROSCLAW_SWARM_AGENTS_JSON env var."""
    raw = os.getenv("ROSCLAW_SWARM_AGENTS_JSON")
    if not raw:
        return []
    data = json.loads(raw)
    agents: List[AgentCapabilities] = []
    for item in data:
        caps = [Capability(**c) for c in item.pop("capabilities", [])]
        agents.append(AgentCapabilities(capabilities=caps, **item))
    return agents


def build_manager() -> SwarmRuntimeManager:
    """Build and pre-populate a SwarmRuntimeManager."""
    mgr = SwarmRuntimeManager()

    # Register agents from environment (optional)
    for agent in load_agents_from_env():
        mgr.register_agent(agent)

    # If no agents registered, emit a warning but still start
    if not mgr.agent_registry.list_all():
        print(
            "[SWARM SERVER] Warning: no agents registered. "
            "Set ROSCLAW_SWARM_AGENTS_JSON or register agents via API.",
            file=sys.stderr,
        )

    return mgr


def main(argv: List[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        prog="rosclaw-swarm-server",
        description="ROSClaw Swarm MCP Server",
    )
    parser.add_argument(
        "--transport",
        choices=["stdio", "sse"],
        default="stdio",
        help="MCP transport protocol (default: stdio)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port for SSE transport (default: 8000)",
    )
    parser.add_argument(
        "--agents",
        type=str,
        default=None,
        help="Path to JSON file with agent definitions",
    )
    args = parser.parse_args(argv)

    # Optional: load agents from file
    if args.agents:
        with open(args.agents) as f:
            os.environ["ROSCLAW_SWARM_AGENTS_JSON"] = f.read()

    mgr = build_manager()

    try:
        from fastmcp import FastMCP
    except ImportError as e:
        print(
            "[SWARM SERVER] fastmcp is required. Install with: pip install rosclaw-swarm[mcp]",
            file=sys.stderr,
        )
        raise SystemExit(1) from e

    mcp = FastMCP("rosclaw-swarm")
    server = SwarmMCPServer(mgr)
    server.mount(mcp)

    print(f"[SWARM SERVER] Online. Transport={args.transport}. Agents={len(mgr.agent_registry.list_all())}")

    if args.transport == "stdio":
        mcp.run(transport="stdio")
    else:
        mcp.run(transport="sse", port=args.port)


if __name__ == "__main__":
    main()
