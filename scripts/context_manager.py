#!/usr/bin/env python3
import argparse
import json
import os
import shutil
import subprocess
from datetime import datetime

LEDGER_FILE = ".council/ledger.json"
NOTES_FILE = ".council/NOTES.md"

def compact_ledger():
    """Moves 'completed' tasks from ledger.json to NOTES.md to free up context."""
    if not os.path.exists(LEDGER_FILE):
        print("⚠️ Ledger file not found.")
        return

    with open(LEDGER_FILE, 'r') as f:
        data = json.load(f)

    active_tasks = []
    completed_tasks = []

    for task in data.get("tasks", []):
        if task.get("status") == "completed":
            completed_tasks.append(task)
        else:
            active_tasks.append(task)

    if not completed_tasks:
        print("ℹ️ No completed tasks to compact.")
        return

    # Append to NOTES.md
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(NOTES_FILE, 'a') as f:
        f.write(f"\n## Compaction Run: {timestamp}\n")
        for task in completed_tasks:
            f.write(f"- **{task['id']}**: {task['description']} (Agent: {task.get('agent')})\n")

    # Update Ledger
    data["tasks"] = active_tasks
    with open(LEDGER_FILE, 'w') as f:
        json.dump(data, f, indent=2)

    print(f"✅ Compacted {len(completed_tasks)} tasks to {NOTES_FILE}.")

def rewind_to_safe_state(force: bool = False) -> bool:
    """
    Rewinds git state to the last commit where Wald Score was >= 0.95.
    (Mock implementation: currently rewinds to HEAD~1 if verification fails)
    """
    if not force:
        print("❌ Rewind blocked by governance. Re-run with --force to confirm.")
        return False

    # In a real implementation, we would tag commits with 'wald-verified'
    # and reset to the latest tag.
    print("🔄 Rewinding to last safe state (HEAD~1)...")
    try:
        subprocess.run(["git", "reset", "--hard", "HEAD~1"], check=True)
        print("✅ Rewind successful.")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Rewind failed: {e}")
        return False

def rollover_session():
    """
    Archives current ledger and starts a new one with a lineage link.
    """
    if not os.path.exists(LEDGER_FILE):
        print("⚠️ No ledger to rollover.")
        return

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    archive_name = f".council/ledger_archive_{timestamp}.json"

    # 1. Archive
    shutil.move(LEDGER_FILE, archive_name)
    print(f"📦 Archived current session to {archive_name}")

    # 2. Create New with Lineage
    new_ledger = {
        "parent": archive_name,
        "created_at": timestamp,
        "tasks": []
    }

    with open(LEDGER_FILE, 'w') as f:
        json.dump(new_ledger, f, indent=2)

    print("✅ Started new session (Lineage Linked).")

def main():
    parser = argparse.ArgumentParser(description="Context Manager (GC)")
    parser.add_argument("action", choices=["compact", "rewind", "rollover"], help="Action to perform")
    parser.add_argument(
        "--force",
        action="store_true",
        help="Required for destructive actions like rewind",
    )

    args = parser.parse_args()

    if args.action == "compact":
        compact_ledger()
    elif args.action == "rewind":
        ok = rewind_to_safe_state(force=args.force)
        if not ok:
            raise SystemExit(2)
    elif args.action == "rollover":
        rollover_session()

if __name__ == "__main__":
    main()
