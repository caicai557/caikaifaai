#!/usr/bin/env python3
import argparse
import os
import sqlite3
import sys

# Import VectorMemory (unified vector storage)
try:
    from council.memory.vector_memory import VectorMemory

    VECTOR_AVAILABLE = True
except ImportError:
    VECTOR_AVAILABLE = False
    print(
        "⚠️ VectorMemory not available. Running in SQL-only mode.",
        file=sys.stderr,
    )

KB_FILE = ".council/playbook.db"


def init_db():
    """Initialize the SQLite knowledge base."""
    conn = sqlite3.connect(KB_FILE)
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS lessons
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  tags TEXT,
                  problem TEXT,
                  solution TEXT,
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)""")
    conn.commit()
    conn.close()


def add_lesson(tags: str, problem: str, solution: str):
    """Add a new lesson to the knowledge base (SQL + Vector)."""
    # 1. Write to SQL
    conn = sqlite3.connect(KB_FILE)
    c = conn.cursor()
    c.execute(
        "INSERT INTO lessons (tags, problem, solution) VALUES (?, ?, ?)",
        (tags, problem, solution),
    )
    lesson_id = c.lastrowid
    conn.commit()
    conn.close()

    print(f"✅ Lesson added to SQL: [{tags}] {problem[:30]}...")

    # 2. Write to Vector Store
    if VECTOR_AVAILABLE:
        try:
            vs = VectorMemory(persist_dir=".council/vectors", collection_name="lessons")
            # Combine problem and solution for embedding
            full_text = f"Problem: {problem}\nSolution: {solution}"
            metadata = {"tags": tags, "source": "user"}
            vs.add(text=full_text, metadata=metadata, doc_id=str(lesson_id))
            print(f"✅ Lesson added to VectorMemory (ID: {lesson_id})")
        except Exception as e:
            print(f"⚠️ Failed to add to VectorMemory: {e}", file=sys.stderr)


def search_lessons(query: str):
    """Search lessons by tags or content (Hybrid: SQL + Vector)."""
    results_map = {}  # Map ID -> Lesson Data to deduplicate

    # 1. SQL Search (Keyword)
    conn = sqlite3.connect(KB_FILE)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    search_term = f"%{query}%"
    c.execute(
        "SELECT * FROM lessons WHERE tags LIKE ? OR problem LIKE ? OR solution LIKE ?",
        (search_term, search_term, search_term),
    )

    sql_results = c.fetchall()
    for row in sql_results:
        results_map[row["id"]] = dict(row)
        results_map[row["id"]]["source"] = "SQL (Keyword)"

    conn.close()

    # 2. Vector Search (Semantic)
    if VECTOR_AVAILABLE:
        try:
            vs = VectorMemory(persist_dir=".council/vectors", collection_name="lessons")
            vector_results = vs.search(query, k=3)

            # VectorMemory returns list of dicts
            for item in vector_results:
                lid = item.get("id")
                if lid:
                    lid_int = int(lid)
                    if lid_int not in results_map:
                        c = conn.cursor()
                        c.execute("SELECT * FROM lessons WHERE id = ?", (lid_int,))
                        row = c.fetchone()
                        if row:
                            results_map[lid_int] = dict(row)
                            distance = item.get("distance", 0)
                            results_map[lid_int]["source"] = (
                                f"Vector (Dist: {distance:.2f})"
                            )
        except Exception as e:
            print(f"⚠️ Vector search failed: {e}", file=sys.stderr)

    # 3. Display Results
    if not results_map:
        print("ℹ️ No lessons found.")
    else:
        print(f"🔍 Found {len(results_map)} lessons:")
        for lid, row in results_map.items():
            print(f"\n--- Lesson #{lid} [{row.get('source', 'Unknown')}] ---")
            print(f"🏷️ Tags: {row['tags']}")
            print(f"❓ Problem: {row['problem']}")
            print(f"💡 Solution: {row['solution']}")


def main():
    parser = argparse.ArgumentParser(description="Collective Memory (Playbook)")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Add
    add_parser = subparsers.add_parser("add", help="Add a lesson")
    add_parser.add_argument("--tags", required=True, help="Comma-separated tags")
    add_parser.add_argument("--problem", required=True, help="Problem description")
    add_parser.add_argument("--solution", required=True, help="Solution description")

    # Search
    search_parser = subparsers.add_parser("search", help="Search lessons")
    search_parser.add_argument("query", help="Search query")

    args = parser.parse_args()

    init_db()

    if args.command == "add":
        add_lesson(args.tags, args.problem, args.solution)
    elif args.command == "search":
        search_lessons(args.query)


if __name__ == "__main__":
    main()
