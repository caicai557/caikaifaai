"""
Pre-Flight Simulator - Predictive Healing / Digital Twin.

Simulates plan execution before running to detect potential conflicts
by checking against the Knowledge Graph.
"""

import re
from typing import List

from council.memory.knowledge_graph import KnowledgeGraph, RelationType


DELETE_KEYWORDS = ["delete", "rm", "remove", "unlink", "drop"]


def extract_target(step: str) -> str:
    """Extract the target file/entity from a plan step."""
    quoted_match = re.search(r'["\']([^"\']+)["\']', step)
    if quoted_match:
        return quoted_match.group(1)

    words = step.split()

    for word in words:
        if word.lower() in DELETE_KEYWORDS:
            continue
        if word.lower() in ["file", "the", "from", "codebase", "-rf", "-r", "-f"]:
            continue
        if "/" in word or "." in word:
            return word.strip("\"'")

    for word in reversed(words):
        if word.lower() not in DELETE_KEYWORDS and len(word) > 2:
            return word.strip("\"'")

    return ""


def is_delete_operation(step: str) -> bool:
    """Check if a plan step is a delete operation."""
    step_lower = step.lower()
    return any(keyword in step_lower for keyword in DELETE_KEYWORDS)


def find_dependents(kg: KnowledgeGraph, target: str) -> List[str]:
    """Find entities that depend on the target."""
    dependents = []
    target_lower = target.lower()

    target_filename = target.split("/")[-1].lower() if "/" in target else target_lower

    for entity_id, entity in kg.entities.items():
        related = kg.get_related(entity_id, direction="from")
        for related_entity, relation in related:
            if relation.relation_type in [
                RelationType.DEPENDS_ON,
                RelationType.IMPORTS,
            ]:
                related_name = related_entity.name.lower()
                related_id = related_entity.id.lower()

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
    """Check Python syntax without executing."""
    try:
        compile(code, "<string>", "exec")
        return []
    except SyntaxError as e:
        return [f"SyntaxError: {e.msg} at line {e.lineno}"]
    except Exception as e:
        return [f"Error: {str(e)}"]


def simulate_plan(
    plan: List[str], kg: KnowledgeGraph, dry_run: bool = False
) -> List[str]:
    """Simulate plan execution and detect potential conflicts."""
    warnings = []

    for step in plan:
        if is_delete_operation(step):
            target = extract_target(step)
            if not target:
                continue

            dependents = find_dependents(kg, target)

            if dependents:
                warning = f"[DEP_CONFLICT] Risk: Deleting '{target}' may break dependent files: {dependents}"
                warnings.append(warning)

        if dry_run and "update" in step.lower() and ".py" in step.lower():
            pass

    return warnings


__all__ = [
    "simulate_plan",
    "extract_target",
    "is_delete_operation",
    "find_dependents",
    "check_syntax",
    "DELETE_KEYWORDS",
]
