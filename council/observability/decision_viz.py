"""
Decision Visualization Module (2026)

Provides visualization tools for agent decision chains:
- Mermaid diagram generation
- HTML report export
- CLI formatted output
- Decision tree rendering
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional
from pathlib import Path


@dataclass
class DecisionNode:
    """
    A node in a decision tree.

    Attributes:
        id: Unique node identifier
        agent: Agent that made the decision
        decision: The decision made
        rationale: Why this decision was made
        confidence: Confidence level (0-1)
        timestamp: When the decision was made
        children: Child decision nodes
        metadata: Additional metadata
    """
    id: str
    agent: str
    decision: str
    rationale: str = ""
    confidence: float = 0.0
    timestamp: Optional[str] = None
    children: List["DecisionNode"] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def add_child(self, child: "DecisionNode") -> None:
        """Add a child decision node."""
        self.children.append(child)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "agent": self.agent,
            "decision": self.decision,
            "rationale": self.rationale,
            "confidence": self.confidence,
            "timestamp": self.timestamp,
            "children": [c.to_dict() for c in self.children],
            "metadata": self.metadata,
        }


class DecisionVisualizer:
    """
    Visualizer for agent decision chains (2026).

    Provides multiple output formats:
    - Mermaid diagrams
    - HTML reports
    - CLI formatted output
    - JSON export

    Example:
        viz = DecisionVisualizer()

        # Add decisions
        viz.add_decision("planner", "Break into subtasks", confidence=0.9)
        viz.add_decision("router", "Use Claude for planning", confidence=0.85)
        viz.add_decision("executor", "Execute code generation", confidence=0.8)

        # Generate outputs
        print(viz.to_mermaid())
        viz.export_html("decisions.html")
    """

    def __init__(self, title: str = "Decision Chain"):
        self.title = title
        self.decisions: List[DecisionNode] = []
        self._node_counter = 0

    def add_decision(
        self,
        agent: str,
        decision: str,
        rationale: str = "",
        confidence: float = 0.0,
        parent_id: Optional[str] = None,
        **metadata,
    ) -> str:
        """
        Add a decision to the chain.

        Args:
            agent: Agent making the decision
            decision: The decision text
            rationale: Reasoning behind the decision
            confidence: Confidence level (0-1)
            parent_id: Optional parent node ID for tree structure
            metadata: Additional metadata

        Returns:
            str: The node ID
        """
        self._node_counter += 1
        node_id = f"D{self._node_counter}"

        node = DecisionNode(
            id=node_id,
            agent=agent,
            decision=decision,
            rationale=rationale,
            confidence=confidence,
            timestamp=datetime.now().isoformat(),
            metadata=metadata,
        )

        if parent_id:
            parent = self._find_node(parent_id)
            if parent:
                parent.add_child(node)
            else:
                self.decisions.append(node)
        else:
            self.decisions.append(node)

        return node_id

    def _find_node(self, node_id: str) -> Optional[DecisionNode]:
        """Find a node by ID (DFS)."""
        def search(nodes: List[DecisionNode]) -> Optional[DecisionNode]:
            for node in nodes:
                if node.id == node_id:
                    return node
                found = search(node.children)
                if found:
                    return found
            return None
        return search(self.decisions)

    def to_mermaid(self, direction: str = "TD") -> str:
        """
        Generate Mermaid diagram.

        Args:
            direction: Graph direction (TD=top-down, LR=left-right)

        Returns:
            str: Mermaid diagram markup
        """
        lines = [f"graph {direction}"]

        def render_node(node: DecisionNode, parent_id: Optional[str] = None) -> None:
            # Escape special characters
            label = node.decision.replace('"', "'")[:40]
            conf_pct = int(node.confidence * 100)

            # Style based on confidence
            if node.confidence >= 0.8:
                shape = f"{node.id}[[\"{node.agent}: {label}\n({conf_pct}%)\"]]"
            elif node.confidence >= 0.5:
                shape = f"{node.id}[\"{node.agent}: {label}\n({conf_pct}%)\"]"
            else:
                shape = f"{node.id}([\"{node.agent}: {label}\n({conf_pct}%)\"])"

            lines.append(f"    {shape}")

            if parent_id:
                lines.append(f"    {parent_id} --> {node.id}")

            for child in node.children:
                render_node(child, node.id)

        # Render chain
        prev_id = None
        for node in self.decisions:
            render_node(node, prev_id)
            if not node.children:
                prev_id = node.id

        # Add styling
        lines.extend([
            "",
            "    classDef high fill:#90EE90,stroke:#228B22",
            "    classDef medium fill:#FFD700,stroke:#DAA520",
            "    classDef low fill:#FFA07A,stroke:#CD5C5C",
        ])

        # Apply styles
        high_nodes = []
        medium_nodes = []
        low_nodes = []

        def categorize(node: DecisionNode):
            if node.confidence >= 0.8:
                high_nodes.append(node.id)
            elif node.confidence >= 0.5:
                medium_nodes.append(node.id)
            else:
                low_nodes.append(node.id)
            for child in node.children:
                categorize(child)

        for node in self.decisions:
            categorize(node)

        if high_nodes:
            lines.append(f"    class {','.join(high_nodes)} high")
        if medium_nodes:
            lines.append(f"    class {','.join(medium_nodes)} medium")
        if low_nodes:
            lines.append(f"    class {','.join(low_nodes)} low")

        return "\n".join(lines)

    def to_cli(self, use_color: bool = True) -> str:
        """
        Generate CLI formatted output.

        Args:
            use_color: Whether to use ANSI colors

        Returns:
            str: CLI formatted text
        """
        lines = [f"=== {self.title} ===", ""]

        def color(text: str, code: str) -> str:
            if use_color:
                return f"\033[{code}m{text}\033[0m"
            return text

        def render_node(node: DecisionNode, indent: int = 0) -> None:
            prefix = "│   " * indent + "├── " if indent > 0 else ""

            # Color based on confidence
            if node.confidence >= 0.8:
                conf_text = color(f"[{node.confidence:.0%}]", "92")  # Green
            elif node.confidence >= 0.5:
                conf_text = color(f"[{node.confidence:.0%}]", "93")  # Yellow
            else:
                conf_text = color(f"[{node.confidence:.0%}]", "91")  # Red

            agent_text = color(node.agent, "94")  # Blue

            lines.append(f"{prefix}{agent_text}: {node.decision} {conf_text}")

            if node.rationale:
                rationale_prefix = "│   " * (indent + 1) if indent >= 0 else "    "
                lines.append(f"{rationale_prefix}└─ {color('Rationale:', '90')} {node.rationale}")

            for child in node.children:
                render_node(child, indent + 1)

        for i, node in enumerate(self.decisions):
            if i > 0:
                lines.append("│")
            render_node(node)

        lines.append("")
        lines.append(f"Total decisions: {self._count_decisions()}")

        return "\n".join(lines)

    def _count_decisions(self) -> int:
        """Count total decisions."""
        count = 0
        def count_recursive(nodes: List[DecisionNode]):
            nonlocal count
            for node in nodes:
                count += 1
                count_recursive(node.children)
        count_recursive(self.decisions)
        return count

    def to_html(self) -> str:
        """
        Generate HTML report.

        Returns:
            str: HTML content
        """
        mermaid = self.to_mermaid()

        # Build decisions table
        rows = []
        def add_row(node: DecisionNode, depth: int = 0):
            indent = "&nbsp;" * (depth * 4)
            conf_class = "high" if node.confidence >= 0.8 else "medium" if node.confidence >= 0.5 else "low"
            rows.append(f"""
                <tr>
                    <td>{indent}{node.agent}</td>
                    <td>{node.decision}</td>
                    <td>{node.rationale or '-'}</td>
                    <td class="{conf_class}">{node.confidence:.0%}</td>
                    <td>{node.timestamp or '-'}</td>
                </tr>
            """)
            for child in node.children:
                add_row(child, depth + 1)

        for node in self.decisions:
            add_row(node)

        table_rows = "\n".join(rows)

        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{self.title}</title>
    <script src="https://cdn.jsdelivr.net/npm/mermaid/dist/mermaid.min.js"></script>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            margin: 0;
            padding: 20px;
            background: #f5f5f5;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
        }}
        h1 {{
            color: #333;
            border-bottom: 2px solid #007bff;
            padding-bottom: 10px;
        }}
        .section {{
            background: white;
            border-radius: 8px;
            padding: 20px;
            margin: 20px 0;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        h2 {{
            color: #555;
            margin-top: 0;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 10px;
        }}
        th, td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }}
        th {{
            background: #f8f9fa;
            font-weight: 600;
        }}
        tr:hover {{
            background: #f8f9fa;
        }}
        .high {{ color: #28a745; font-weight: bold; }}
        .medium {{ color: #ffc107; font-weight: bold; }}
        .low {{ color: #dc3545; font-weight: bold; }}
        .mermaid {{
            text-align: center;
            padding: 20px;
        }}
        .stats {{
            display: flex;
            gap: 20px;
            flex-wrap: wrap;
        }}
        .stat-card {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 8px;
            min-width: 150px;
        }}
        .stat-value {{
            font-size: 2em;
            font-weight: bold;
        }}
        .stat-label {{
            opacity: 0.9;
        }}
        .timestamp {{
            color: #888;
            font-size: 0.9em;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🤖 {self.title}</h1>
        <p class="timestamp">Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>

        <div class="section">
            <h2>📊 Summary</h2>
            <div class="stats">
                <div class="stat-card">
                    <div class="stat-value">{self._count_decisions()}</div>
                    <div class="stat-label">Decisions</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">{len(set(n.agent for n in self._all_nodes()))}</div>
                    <div class="stat-label">Agents</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">{self._avg_confidence():.0%}</div>
                    <div class="stat-label">Avg Confidence</div>
                </div>
            </div>
        </div>

        <div class="section">
            <h2>🔀 Decision Flow</h2>
            <div class="mermaid">
{mermaid}
            </div>
        </div>

        <div class="section">
            <h2>📝 Decision Details</h2>
            <table>
                <thead>
                    <tr>
                        <th>Agent</th>
                        <th>Decision</th>
                        <th>Rationale</th>
                        <th>Confidence</th>
                        <th>Timestamp</th>
                    </tr>
                </thead>
                <tbody>
                    {table_rows}
                </tbody>
            </table>
        </div>
    </div>

    <script>
        mermaid.initialize({{ startOnLoad: true, theme: 'default' }});
    </script>
</body>
</html>
"""
        return html

    def _all_nodes(self) -> List[DecisionNode]:
        """Get all nodes flattened."""
        nodes = []
        def collect(node_list: List[DecisionNode]):
            for node in node_list:
                nodes.append(node)
                collect(node.children)
        collect(self.decisions)
        return nodes

    def _avg_confidence(self) -> float:
        """Calculate average confidence."""
        nodes = self._all_nodes()
        if not nodes:
            return 0.0
        return sum(n.confidence for n in nodes) / len(nodes)

    def export_html(self, path: str) -> None:
        """Export HTML report to file."""
        Path(path).write_text(self.to_html(), encoding="utf-8")

    def export_json(self, path: str) -> None:
        """Export decisions to JSON file."""
        data = {
            "title": self.title,
            "generated": datetime.now().isoformat(),
            "total_decisions": self._count_decisions(),
            "decisions": [d.to_dict() for d in self.decisions],
        }
        Path(path).write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")

    def clear(self) -> None:
        """Clear all decisions."""
        self.decisions.clear()
        self._node_counter = 0


def visualize_from_records(records: list, title: str = "Decision Chain") -> DecisionVisualizer:
    """
    Create a visualizer from DecisionRecord list.

    Args:
        records: List of DecisionRecord from StructuredLogger
        title: Visualization title

    Returns:
        DecisionVisualizer instance
    """
    viz = DecisionVisualizer(title)
    for record in records:
        viz.add_decision(
            agent=record.agent if hasattr(record, 'agent') else record.get('agent', 'unknown'),
            decision=record.decision if hasattr(record, 'decision') else record.get('decision', ''),
            rationale=record.rationale if hasattr(record, 'rationale') else record.get('rationale', ''),
            confidence=record.confidence if hasattr(record, 'confidence') else record.get('confidence', 0.0),
        )
    return viz


__all__ = [
    "DecisionNode",
    "DecisionVisualizer",
    "visualize_from_records",
]
