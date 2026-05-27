"""Task Graph visualizer — exports to Mermaid, Graphviz DOT, and ASCII.

No ROS required.  Pure Python.
"""

from __future__ import annotations

from typing import Dict, List, Optional, Set

from rosclaw_swarm.models import TaskGraph, TaskStatus


def to_mermaid(graph: TaskGraph, highlight_assigned: bool = True) -> str:
    """Convert TaskGraph to Mermaid flowchart syntax."""
    lines = ["flowchart TD"]
    assigned: Set[str] = set()

    for task in graph.tasks:
        node_id = task.id.replace("-", "_")
        status_emoji = {
            TaskStatus.PENDING: "⬜",
            TaskStatus.ASSIGNED: "📋",
            TaskStatus.RUNNING: "🔄",
            TaskStatus.COMPLETED: "✅",
            TaskStatus.FAILED: "❌",
            TaskStatus.CANCELLED: "🚫",
        }.get(task.status, "⬜")

        agent = task.token.assigned_agent_id if task.token else "unassigned"
        if task.token:
            assigned.add(task.id)

        label = f"{status_emoji} {task.description}"
        if highlight_assigned and agent != "unassigned":
            label += f"\\n👤 {agent}"

        # Style by status
        style = ""
        if task.status == TaskStatus.COMPLETED:
            style = f"    style {node_id} fill:#90EE90"
        elif task.status == TaskStatus.FAILED:
            style = f"    style {node_id} fill:#FFB6C1"
        elif task.status == TaskStatus.RUNNING:
            style = f"    style {node_id} fill:#87CEEB"
        elif task.token:
            style = f"    style {node_id} fill:#FFD700"

        lines.append(f"    {node_id}[\"{label}\"]")
        if style:
            lines.append(style)

    for task in graph.tasks:
        node_id = task.id.replace("-", "_")
        for dep in task.dependencies:
            dep_id = dep.replace("-", "_")
            lines.append(f"    {dep_id} --> {node_id}")

    return "\n".join(lines)


def to_dot(graph: TaskGraph, highlight_assigned: bool = True) -> str:
    """Convert TaskGraph to Graphviz DOT syntax."""
    lines = ["digraph TaskGraph {", '    rankdir="TB";', '    node [shape=box, style="rounded,filled", fontname="Helvetica"];']

    for task in graph.tasks:
        agent = task.token.assigned_agent_id if task.token else "unassigned"
        label = f"{task.description}\\n({task.capability or 'none'})"
        if highlight_assigned and agent != "unassigned":
            label += f"\\n[{agent}]"

        color = {
            TaskStatus.PENDING: "white",
            TaskStatus.ASSIGNED: "gold",
            TaskStatus.RUNNING: "skyblue",
            TaskStatus.COMPLETED: "palegreen",
            TaskStatus.FAILED: "lightcoral",
            TaskStatus.CANCELLED: "lightgray",
        }.get(task.status, "white")

        lines.append(f'    "{task.id}" [label="{label}", fillcolor={color}];')

    for task in graph.tasks:
        for dep in task.dependencies:
            lines.append(f'    "{dep}" -> "{task.id}";')

    lines.append("}")
    return "\n".join(lines)


def to_ascii(graph: TaskGraph) -> str:
    """Simple ASCII tree representation."""
    lines: List[str] = [f"TaskGraph: {graph.goal}", "=" * 40]

    # Build adjacency
    children: Dict[str, List[str]] = {t.id: [] for t in graph.tasks}
    roots: List[str] = []
    for task in graph.tasks:
        if not task.dependencies:
            roots.append(task.id)
        for dep in task.dependencies:
            children.setdefault(dep, []).append(task.id)

    def render(node_id: str, prefix: str = "", is_last: bool = True) -> None:
        task = graph.get_task(node_id)
        if not task:
            return
        connector = "└── " if is_last else "├── "
        agent = task.token.assigned_agent_id if task.token else "?"
        status = task.status.value[:3].upper()
        lines.append(f"{prefix}{connector}[{status}] {task.description} ({task.capability or 'none'}) -> {agent}")
        child_prefix = prefix + ("    " if is_last else "│   ")
        child_ids = children.get(node_id, [])
        for i, child_id in enumerate(child_ids):
            render(child_id, child_prefix, i == len(child_ids) - 1)

    for i, root_id in enumerate(roots):
        render(root_id, "", i == len(roots) - 1)

    return "\n".join(lines)
