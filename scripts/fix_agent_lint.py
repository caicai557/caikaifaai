#!/usr/bin/env python3
"""
PTC Script: Fix lint errors in Agent test files
Batch operation to remove unused imports and fix unused variables.
"""

import re
import os


def fix_unused_qa_variable(filepath: str) -> int:
    """Fix unused 'qa' variable by adding _ prefix or using it."""
    with open(filepath, "r") as f:
        content = f.read()

    # Pattern: qa = QAAgent(...) where qa is unused
    # Fix by adding underscore prefix or removing
    original = content
    content = re.sub(
        r"^(\s+)qa = (QAAgent\(.*?\))\s*$",
        r"\1_ = \2  # noqa: F841",
        content,
        flags=re.MULTILINE,
    )

    if content != original:
        with open(filepath, "w") as f:
            f.write(content)
        return 1
    return 0


def fix_unused_orch_variable(filepath: str) -> int:
    """Fix unused 'orch' variable."""
    with open(filepath, "r") as f:
        content = f.read()

    original = content
    content = re.sub(
        r"^(\s+)orch = (OrchestratorAgent\(.*?\))\s*$",
        r"\1_ = \2  # noqa: F841",
        content,
        flags=re.MULTILINE,
    )

    if content != original:
        with open(filepath, "w") as f:
            f.write(content)
        return 1
    return 0


def remove_unused_event_import(filepath: str) -> int:
    """Remove unused Event import."""
    with open(filepath, "r") as f:
        content = f.read()

    original = content
    # Replace "Event, EventType" with just "EventType" if Event is unused
    content = re.sub(
        r"from council\.orchestration\.events import Event, EventType",
        "from council.orchestration.events import EventType",
        content,
    )

    if content != original:
        with open(filepath, "w") as f:
            f.write(content)
        return 1
    return 0


def main():
    fixes = 0
    test_dir = "tests"

    files_to_fix = [
        "test_qa.py",
        "test_planner.py",
        "test_orchestrator_hub.py",
    ]

    for filename in files_to_fix:
        filepath = os.path.join(test_dir, filename)
        if os.path.exists(filepath):
            if "qa" in filename:
                fixes += fix_unused_qa_variable(filepath)
                fixes += remove_unused_event_import(filepath)
            elif "planner" in filename:
                fixes += remove_unused_event_import(filepath)
            elif "orchestrator" in filename:
                fixes += fix_unused_orch_variable(filepath)

    print(f"Fixed {fixes} files")


if __name__ == "__main__":
    main()
