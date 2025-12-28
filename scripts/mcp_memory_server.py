#!/usr/bin/env python3
import json
import os
import sqlite3
import sys
from typing import Optional
from mcp.server.fastmcp import FastMCP

# Initialize FastMCP server
mcp = FastMCP("CouncilMemory")

# Constants
LEDGER_FILE = ".council/ledger.json"
PERMISSIONS_FILE = ".council/permissions.json"

# In-Memory Database Setup
db = sqlite3.connect(":memory:", check_same_thread=False)
db.row_factory = sqlite3.Row


def init_db():
    """Initialize in-memory schema and load from disk if exists."""
    db.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id TEXT PRIMARY KEY,
            description TEXT NOT NULL,
            status TEXT DEFAULT 'pending',
            agent TEXT DEFAULT 'Gemini',
            confidence REAL DEFAULT 0.0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Load from disk
    if os.path.exists(LEDGER_FILE):
        try:
            with open(LEDGER_FILE, "r") as f:
                data = json.load(f)
                for task in data.get("tasks", []):
                    db.execute(
                        "INSERT OR IGNORE INTO tasks (id, description, status, agent, confidence, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
                        (
                            task["id"],
                            task["description"],
                            task["status"],
                            task["agent"],
                            task.get("confidence", 0.0),
                            task.get("created_at"),
                            task.get("updated_at"),
                        ),
                    )
            print(
                f"✅ Loaded {len(data.get('tasks', []))} tasks from disk into memory.",
                file=sys.stderr,
            )
        except Exception as e:
            print(f"⚠️ Failed to load ledger: {e}", file=sys.stderr)


def persist_to_disk():
    """Flush in-memory state to JSON file."""
    cursor = db.execute("SELECT * FROM tasks")
    tasks = [dict(row) for row in cursor.fetchall()]

    os.makedirs(os.path.dirname(LEDGER_FILE), exist_ok=True)
    with open(LEDGER_FILE, "w") as f:
        json.dump({"tasks": tasks}, f, indent=2)
    print("💾 Persisted state to disk.", file=sys.stderr)


def check_permission(agent_id: str, permission: str) -> bool:
    """Check if agent has required permission."""
    if not os.path.exists(PERMISSIONS_FILE):
<<<<<<< HEAD
        return True # Default allow if no policy
=======
        return True  # Default allow if no policy
>>>>>>> e2df45bcf4fae044c2ec81c7ea50a183bdc8bd86

    try:
        with open(PERMISSIONS_FILE, "r") as f:
            policy = json.load(f)

        role_def = policy.get("roles", {}).get(agent_id.lower())
        if not role_def:
            # Fallback to default role
            default_role = policy.get("default_role", "claude")
            role_def = policy.get("roles", {}).get(default_role)

        if role_def and permission in role_def.get("permissions", []):
            return True

        return False
    except Exception:
        return False


# --- Resources ---


@mcp.resource("council://ledger")
def get_ledger() -> str:
    """Get the full task ledger state."""
    cursor = db.execute("SELECT * FROM tasks")
    tasks = [dict(row) for row in cursor.fetchall()]
    return json.dumps({"tasks": tasks}, indent=2)


# --- Tools ---


@mcp.tool()
def add_task(description: str, agent: str = "Gemini", agent_id: str = "claude") -> str:
    """Add a new task to the ledger."""
    if not check_permission(agent_id, "update_task"):
        return f"❌ Permission Denied: Agent '{agent_id}' cannot 'update_task'."

    cursor = db.execute("SELECT COUNT(*) FROM tasks")
    count = cursor.fetchone()[0]
    task_id = f"T-{count + 1}"

    db.execute(
        "INSERT INTO tasks (id, description, agent) VALUES (?, ?, ?)",
        (task_id, description, agent),
    )
    persist_to_disk()
    return f"✅ Task {task_id} added."


@mcp.tool()
def update_task(
    task_id: str,
    status: Optional[str] = None,
    confidence: Optional[float] = None,
    agent_id: str = "claude",
) -> str:
    """Update an existing task."""
    if not check_permission(agent_id, "update_task"):
        return f"❌ Permission Denied: Agent '{agent_id}' cannot 'update_task'."

    updates = []
    params = []

    if status:
        updates.append("status = ?")
        params.append(status)
    if confidence is not None:
        updates.append("confidence = ?")
        params.append(confidence)

    if not updates:
        return "⚠️ No updates provided."

    updates.append("updated_at = CURRENT_TIMESTAMP")
    params.append(task_id)

    query = f"UPDATE tasks SET {', '.join(updates)} WHERE id = ?"
    cursor = db.execute(query, params)

    if cursor.rowcount > 0:
        persist_to_disk()
        return f"✅ Task {task_id} updated."
    else:
        return f"❌ Task {task_id} not found."


if __name__ == "__main__":
    init_db()
    mcp.run()
