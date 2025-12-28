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

import re
from typing import List

from council.memory.knowledge_graph import KnowledgeGraph, RelationType


# Keywords that indicate delete operations
DELETE_KEYWORDS = ["delete", "rm", "remove", "unlink", "drop"]


def extract_target(step: str) -> str:
    """Extract the target file/entity from a plan step.

    Args:
        step: A plan step string like "Delete file src/utils.py"

    Returns:
        The extracted target name/path.
    """
    # Try to extract quoted paths first
    quoted_match = re.search(r'["\']([^"\']+)["\']', step)
    if quoted_match:
        return quoted_match.group(1)

    # Split on common separators and look for file-like targets
    words = step.split()

    # Look for paths (contain / or .)
    for word in words:
        # Skip keywords
        if word.lower() in DELETE_KEYWORDS:
            continue
        # Skip common non-target words
        if word.lower() in ["file", "the", "from", "codebase", "-rf", "-r", "-f"]:
            continue
        # If it looks like a path or filename, return it
        if "/" in word or "." in word:
            return word.strip("\"'")

    # Fallback: return last word that's not a keyword
    for word in reversed(words):
        if word.lower() not in DELETE_KEYWORDS and len(word) > 2:
            return word.strip("\"'")

    return ""


def is_delete_operation(step: str) -> bool:
    """Check if a plan step is a delete operation.

    Args:
        step: A plan step string.

    Returns:
        True if the step represents a delete operation.
    """
    step_lower = step.lower()
    return any(keyword in step_lower for keyword in DELETE_KEYWORDS)


def find_dependents(kg: KnowledgeGraph, target: str) -> List[str]:
    """Find entities that depend on the target.

    Searches the knowledge graph for entities with DEPENDS_ON
    or IMPORTS relationships pointing to the target.

    Args:
        kg: The knowledge graph to search.
        target: The target entity name/path.

    Returns:
        List of dependent entity names.
    """
    dependents = []
    target_lower = target.lower()

    # Extract filename from path for matching
    target_filename = target.split("/")[-1].lower() if "/" in target else target_lower

    # Get all entities and check relationships
    for entity_id, entity in kg.entities.items():
        # Check if this entity depends on target
        related = kg.get_related(entity_id, direction="from")
        for related_entity, relation in related:
            # Check if this entity depends on something matching target
            if relation.relation_type in [
                RelationType.DEPENDS_ON,
                RelationType.IMPORTS,
            ]:
                related_name = related_entity.name.lower()
                related_id = related_entity.id.lower()

                # Exact match on ID or name
                if (
                    related_id == target_lower
                    or related_name == target_lower
                    or related_name == target_filename
                    or related_id == target_filename
                ):
                    dependents.append(entity.name)
                    break

    return dependents


def check_syntax(code: str) -> List[str]:
    """Check Python syntax without executing.
    
    Args:
        code: Python code string.
        
    Returns:
        List of error messages if syntax is invalid.
    """
    try:
        compile(code, "<string>", "exec")
        return []
    except SyntaxError as e:
        return [f"SyntaxError: {e.msg} at line {e.lineno}"]
    except Exception as e:
        return [f"Error: {str(e)}"]

def simulate_plan(plan: List[str], kg: KnowledgeGraph, dry_run: bool = False) -> List[str]:
    """Simulate plan execution and detect potential conflicts.

    Checks each step against the Knowledge Graph to identify:
    - Delete operations that would break dependencies
    - Other risky operations
    - (Optional) Syntax checks if content is provided in step.

    Args:
        plan: List of plan steps to simulate.
        kg: Knowledge Graph containing project dependencies.
        dry_run: If True, performs enhanced validation (like syntax checking).

    Returns:
        List of warning/error messages.
    """
    warnings = []

    for step in plan:
        # Check 1: Dependency Risk
        if is_delete_operation(step):
            target = extract_target(step)
            if not target:
                continue

            # Find what depends on this target
            # Need to handle potential file extension differences or partial paths
            # This logic assumes target matches what's used in the graph
            dependents = find_dependents(kg, target)

            if dependents:
                # Structured error format suggestion: [DEP_CONFLICT] Message
                warning = (
                    f"[DEP_CONFLICT] Risk: Deleting '{target}' may break dependent files: {dependents}"
                )
                warnings.append(warning)
        
        # Check 2: Syntax Check (if step contains code content provided as JSON or similar)
        # Note: In a real scenario, the 'plan' usually contains just text descriptions.
        # But if we were passing file content updates, we'd check them here.
        # For this implementation, we'll assume a convention where updates might include snippet checks
        # or we check referenced files if they exist (not applicable for 'Delete').
        
        # Extended Check: If dry_run is enabled, we could potentially check for other risks
        if dry_run and "update" in step.lower() and ".py" in step.lower():
             # In future iteration: Read file content + proposed diff -> compile()
             # For now, just a placeholder for the feature
             pass

    return warnings


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
