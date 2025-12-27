#!/usr/bin/env python3
"""
Batch Replace Tool - Token-efficient code modifications.

Usage:
    python scripts/batch_replace.py --pattern "old" --replacement "new" --glob "src/**/*.py"
"""

import argparse
import glob
import re
import sys


def batch_replace(
    pattern: str, replacement: str, file_glob: str = "**/*.py", dry_run: bool = False
) -> int:
    """
    Batch replace pattern in files.

    Args:
        pattern: Regex pattern to match
        replacement: Replacement string
        file_glob: Glob pattern for files
        dry_run: If True, only show what would be changed

    Returns:
        Number of files changed
    """
    files_changed = 0

    for filepath in glob.glob(file_glob, recursive=True):
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                original = f.read()
        except (UnicodeDecodeError, IOError):
            continue

        modified = re.sub(pattern, replacement, original, flags=re.MULTILINE)

        if modified != original:
            if dry_run:
                print(f"[DRY RUN] Would modify: {filepath}")
            else:
                with open(filepath, "w", encoding="utf-8") as f:
                    f.write(modified)
                print(f"✅ Modified: {filepath}")
            files_changed += 1

    print(f"\n{'Would modify' if dry_run else 'Modified'}: {files_changed} file(s)")
    return files_changed


def main():
    parser = argparse.ArgumentParser(
        description="Batch replace tool for token-efficient modifications"
    )
    parser.add_argument("--pattern", "-p", required=True, help="Regex pattern to match")
    parser.add_argument("--replacement", "-r", required=True, help="Replacement string")
    parser.add_argument(
        "--glob", "-g", default="**/*.py", help="File glob pattern (default: **/*.py)"
    )
    parser.add_argument(
        "--dry-run",
        "-n",
        action="store_true",
        help="Show what would be changed without modifying",
    )

    args = parser.parse_args()

    count = batch_replace(args.pattern, args.replacement, args.glob, args.dry_run)
    sys.exit(0 if count >= 0 else 1)


if __name__ == "__main__":
    main()
