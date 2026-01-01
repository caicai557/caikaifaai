#!/usr/bin/env python3
"""
Pre-Flight Simulator - Predictive Healing / Digital Twin.

Simulates plan execution before running to detect potential conflicts
by checking against the Knowledge Graph.

Usage:
    from scripts.simulate import simulate_plan
    from council.memory.knowledge_graph import KnowledgeGraph

    kg = KnowledgeGraph()
    # ... populate kg with project dependencies ...

    plan = ["Delete utils.py", "Refactor main.py"]
    warnings = simulate_plan(plan, kg)

    if warnings:
        print("Potential issues detected:")
        for w in warnings:
            print(f"  - {w}")
"""

from council.memory.knowledge_graph import KnowledgeGraph
from council.mcp.simulate import (
    DELETE_KEYWORDS,
    check_syntax,
    extract_target,
    find_dependents,
    is_delete_operation,
    simulate_plan,
)


__all__ = [
    "simulate_plan",
    "extract_target",
    "is_delete_operation",
    "find_dependents",
    "check_syntax",
    "DELETE_KEYWORDS",
]


if __name__ == "__main__":
    # Example usage
    print("Pre-Flight Simulator")
    print("=" * 40)

    kg = KnowledgeGraph()

    # Example: simulate a plan
    test_plan = [
        "Delete utils.py",
        "Update main.py",
    ]

    results = simulate_plan(test_plan, kg)
    if results:
        print("Warnings detected:")
        for w in results:
            print(f"  - {w}")
    else:
        print("No issues detected.")
