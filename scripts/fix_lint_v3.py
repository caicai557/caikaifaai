#!/usr/bin/env python3
"""
PTC Script v3: Comprehensive lint fix
Handles ALL remaining lint issues in test files.
"""

import os

FIXES = {
    "tests/test_agent_integration.py": [
        # Remove unused coder variable
        ("coder = CoderAgent(", "CoderAgent("),
        # Remove unused qa variable
        ("qa = QAAgent(", "QAAgent("),
    ],
    "tests/test_base_agent.py": [
        # Remove unused ABC import
        ("from abc import ABC\n", ""),
    ],
    "tests/test_coder.py": [
        # Remove unused coder variable (where not used)
        # Line 23 and 32
    ],
    "tests/test_hitl.py": [
        # Remove unused EventType import
        ("from council.orchestration.events import EventType\n", ""),
    ],
    "tests/test_hub_boundary.py": [
        # Remove unused threading import
        ("import threading\n", ""),
        # Fix long line
        (
            "Verify: Hub handles nested publishing without infinite loop (unless logic dictates).",
            "Verify: Hub handles nested publishing without infinite loop.",
        ),
    ],
    "tests/test_observability.py": [
        # Keep observer but use it
        (
            "observer = HubObserver(hub=self.hub, tracer=tracer)",
            "_ = HubObserver(hub=self.hub, tracer=tracer)  # noqa: F841",
        ),
    ],
}


def fix_file(filepath: str, replacements: list) -> int:
    """Apply replacements to a file."""
    if not os.path.exists(filepath):
        return 0

    with open(filepath, "r") as f:
        content = f.read()

    original = content
    for old, new in replacements:
        content = content.replace(old, new)

    if content != original:
        with open(filepath, "w") as f:
            f.write(content)
        print(f"Fixed: {filepath}")
        return 1
    return 0


def fix_coder_test():
    """Special fix for test_coder.py - keep variable where used."""
    filepath = "tests/test_coder.py"
    with open(filepath, "r") as f:
        lines = f.readlines()

    fixed_lines = []
    for i, line in enumerate(lines):
        # Line 23: coder not used -> remove assignment
        if "coder = CoderAgent(" in line and i < 25:
            fixed_lines.append(line.replace("coder = ", ""))
        # Line 32: coder not used -> remove assignment
        elif "coder = CoderAgent(" in line and 30 < i < 35:
            fixed_lines.append(line.replace("coder = ", ""))
        else:
            fixed_lines.append(line)

    with open(filepath, "w") as f:
        f.writelines(fixed_lines)
    print(f"Fixed: {filepath}")


def main():
    fixes = 0
    for filepath, replacements in FIXES.items():
        if replacements:
            fixes += fix_file(filepath, replacements)

    fix_coder_test()
    fixes += 1

    print(f"Total fixed: {fixes} files")


if __name__ == "__main__":
    main()
