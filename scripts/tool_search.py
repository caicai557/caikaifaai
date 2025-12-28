#!/usr/bin/env python3
"""
Tool Search Tool - Dynamic tool discovery using keyword/vector search.

This implements the "defer_loading" pattern from Anthropic best practices:
- 90% of tools are marked as defer_loading: true
- Only a ~500 token search tool is kept in System Prompt
- Agents search and load 3-5 relevant tools on-demand
"""

import argparse
import json
import os
import sys
from typing import Dict, List

TOOL_REGISTRY_FILE = ".council/tool_registry.json"


def load_registry() -> List[Dict]:
    """Load the tool registry from disk."""
    if os.path.exists(TOOL_REGISTRY_FILE):
        with open(TOOL_REGISTRY_FILE) as f:
            return json.load(f)
    return []


def save_registry(tools: List[Dict]) -> None:
    """Save the tool registry to disk."""
    os.makedirs(os.path.dirname(TOOL_REGISTRY_FILE), exist_ok=True)
    with open(TOOL_REGISTRY_FILE, "w") as f:
        json.dump(tools, f, indent=2)


def register_tool(name: str, description: str, schema: str) -> bool:
    """Register a new tool in the registry."""
    registry = load_registry()

    # Check for duplicates
    for tool in registry:
        if tool.get("name") == name:
            print(
                f"⚠️ Tool '{name}' already exists. Use --force to overwrite.",
                file=sys.stderr,
            )
            return False

    registry.append(
        {
            "name": name,
            "description": description,
            "schema": schema,
            "defer_loading": True,
        }
    )
    save_registry(registry)
    print(f"✅ Registered tool: {name}")
    return True


def search_tools(query: str, top_k: int = 5) -> List[Dict]:
    """
    Search for tools by keyword matching.

    In a production system, this would use vector similarity search.
    For now, we use simple keyword matching as a baseline.
    """
    registry = load_registry()
    results = []
    query_lower = query.lower()

    for tool in registry:
        score = 0
        name = tool.get("name", "").lower()
        desc = tool.get("description", "").lower()

        # Score based on matches
        if query_lower in name:
            score += 3
        if query_lower in desc:
            score += 1

        # Check for partial word matches
        for word in query_lower.split():
            if word in name:
                score += 2
            if word in desc:
                score += 0.5

        if score > 0:
            results.append((score, tool))

    # Sort by score descending
    results.sort(key=lambda x: x[0], reverse=True)
    return [tool for _, tool in results[:top_k]]


def list_tools() -> None:
    """List all registered tools."""
    registry = load_registry()
    if not registry:
        print("ℹ️ No tools registered yet.")
        return

    print(f"📦 Registered Tools ({len(registry)}):\n")
    for tool in registry:
        defer = "🔒" if tool.get("defer_loading") else "🔓"
        print(f"  {defer} {tool['name']}: {tool['description'][:50]}...")


def main():
    parser = argparse.ArgumentParser(
        description="Tool Search Tool - Dynamic tool discovery"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Register
    reg_parser = subparsers.add_parser("register", help="Register a new tool")
    reg_parser.add_argument("--name", required=True, help="Tool name")
    reg_parser.add_argument("--description", required=True, help="Tool description")
    reg_parser.add_argument("--schema", default="{}", help="JSON schema (optional)")

    # Search
    search_parser = subparsers.add_parser("search", help="Search for tools")
    search_parser.add_argument("query", help="Search query")
    search_parser.add_argument("--top-k", type=int, default=5, help="Number of results")

    # List
    subparsers.add_parser("list", help="List all registered tools")

    args = parser.parse_args()

    if args.command == "register":
        register_tool(args.name, args.description, args.schema)
    elif args.command == "search":
        results = search_tools(args.query, args.top_k)
        if results:
            print(f"🔍 Found {len(results)} tools for '{args.query}':\n")
            for tool in results:
                print(f"  📌 {tool['name']}")
                print(f"     {tool['description']}")
                print()
        else:
            print(f"ℹ️ No tools found for '{args.query}'")
    elif args.command == "list":
        list_tools()


if __name__ == "__main__":
    main()
