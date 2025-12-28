#!/usr/bin/env python3
"""
Adjudicator - The Judge.
Builds a Knowledge Graph (KG) of the codebase for semantic validation.
"""

import argparse
import os
import sys
import ast

try:
    import networkx as nx
except ImportError:
    print(
        "❌ networkx is required. Install with: pip install networkx", file=sys.stderr
    )
    raise SystemExit(2)

KG_FILE = ".council/knowledge_graph.gml"


def build_graph(root_dir: str) -> nx.DiGraph:
    """Build a dependency graph from Python files."""
    G = nx.DiGraph()

    print(f"⚖️ Adjudicator: Scanning {root_dir} for Knowledge Graph...")

    for root, _, files in os.walk(root_dir):
        for file in files:
            if file.endswith(".py"):
                file_path = os.path.join(root, file)
                rel_path = os.path.relpath(file_path, root_dir)

                # Add node
                G.add_node(rel_path, type="file")

                try:
                    with open(file_path, "r") as f:
                        tree = ast.parse(f.read())

                    # Analyze imports
                    for node in ast.walk(tree):
                        if isinstance(node, ast.Import):
                            for alias in node.names:
                                G.add_edge(rel_path, alias.name, type="imports")
                        elif isinstance(node, ast.ImportFrom):
                            if node.module:
                                G.add_edge(rel_path, node.module, type="imports")

                except Exception as e:
                    print(f"⚠️ Failed to parse {rel_path}: {e}", file=sys.stderr)

    return G


def validate_change(graph: nx.DiGraph, file_path: str) -> bool:
    """Validate a change against the KG (Mock logic)."""
    # In a real system, this would check for circular dependencies,
    # forbidden imports, or architectural violations.
    if file_path in graph.nodes:
        # Example check: Ensure core scripts don't import from tests
        successors = list(graph.successors(file_path))
        for succ in successors:
            if "tests" in succ:
                print(f"❌ Violation: {file_path} imports from test module {succ}")
                return False
    return True


def main():
    parser = argparse.ArgumentParser(description="Adjudicator (Knowledge Graph)")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Build
    build_parser = subparsers.add_parser("build", help="Build Knowledge Graph")
    build_parser.add_argument("--root", default=".", help="Root directory")

    # Validate
    val_parser = subparsers.add_parser("validate", help="Validate a file")
    val_parser.add_argument("--file", required=True, help="File to validate")

    args = parser.parse_args()

    if args.command == "build":
        G = build_graph(args.root)
        os.makedirs(os.path.dirname(KG_FILE), exist_ok=True)
        nx.write_gml(G, KG_FILE)
<<<<<<< HEAD
        print(f"✅ Knowledge Graph built: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges.")
=======
        print(
            f"✅ Knowledge Graph built: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges."
        )
>>>>>>> e2df45bcf4fae044c2ec81c7ea50a183bdc8bd86

    elif args.command == "validate":
        if os.path.exists(KG_FILE):
            G = nx.read_gml(KG_FILE)
            if validate_change(G, args.file):
                print("✅ Semantic Validation Passed")
            else:
                sys.exit(1)
        else:
            print("⚠️ KG not found. Run 'build' first.")


if __name__ == "__main__":
    main()
