#!/usr/bin/env python3
"""
PTC Script v2: Fix remaining lint errors
- Remove unused imports
- Remove trailing whitespace from blank lines
"""

import re
import glob


def fix_file(filepath: str) -> int:
    """Fix lint issues in a file."""
    with open(filepath, "r") as f:
        content = f.read()

    original = content
    lines = content.split("\n")
    fixed_lines = []

    for line in lines:
        # Remove trailing whitespace from blank lines
        if line.strip() == "" and line != "":
            fixed_lines.append("")
        else:
            fixed_lines.append(line)

    content = "\n".join(fixed_lines)

    # Remove unused imports
    # logging if unused
    if (
        "import logging" in content
        and "logging." not in content
        and "logging)" not in content
    ):
        if "getLogger" not in content:
            content = re.sub(r"^import logging\n", "", content, flags=re.MULTILINE)

    # Event if unused (but EventType is used)
    if "import Event, EventType" in content:
        if content.count("Event(") == 0 and content.count("Event)") == 0:
            content = content.replace(
                "from council.orchestration.events import Event, EventType",
                "from council.orchestration.events import EventType",
            )

    if content != original:
        with open(filepath, "w") as f:
            f.write(content)
        return 1
    return 0


def main():
    fixes = 0
    for filepath in glob.glob("tests/test_*.py"):
        fixes += fix_file(filepath)
    print(f"Fixed {fixes} files")


if __name__ == "__main__":
    main()
