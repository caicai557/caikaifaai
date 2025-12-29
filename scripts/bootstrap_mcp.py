#!/usr/bin/env python3
"""
Bootstrap MCP - Zero-Touch Onboarding Script
Parses `docs/mcp.meta.json` (Hyper-Metadata) and updates `.mcp.json`.
"""

import json
import os
import sys
from pathlib import Path

# Paths
PROJECT_ROOT = Path(__file__).parent.parent
META_PATH = PROJECT_ROOT / "docs" / "mcp.meta.json"
MCP_CONFIG_PATH = PROJECT_ROOT / ".mcp.json"

def load_metadata():
    if not META_PATH.exists():
        print(f"❌ Error: Metadata file not found at {META_PATH}")
        sys.exit(1)

    with open(META_PATH, "r") as f:
        return json.load(f)

def load_local_config():
    if not MCP_CONFIG_PATH.exists():
        return {"mcpServers": {}}

    with open(MCP_CONFIG_PATH, "r") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return {"mcpServers": {}}

def bootstrap():
    print("🚀 Bootstrapping MCP Configuration...")

    meta = load_metadata()
    config = load_local_config()

    updates_count = 0

    # Iterate through defined servers in metadata
    for server_id, server_def in meta.get("servers", {}).items():
        print(f"   Processing server: {server_id}...", end=" ")

        # Check if environment variables are required
        required_env = meta.get("governance", {}).get("required_env", [])
        env_vars = {}
        missing_vars = []

        for var in required_env:
            if var not in os.environ:
                missing_vars.append(var)
            else:
                env_vars[var] = os.environ[var]

        if missing_vars:
            print(f"⚠️  Missing Env Vars: {missing_vars}")
            # We still generate the config, but warn the user

        # Construct the MCP server configuration
        # We assume command is relative to project root, so we check usage
        cmd = server_def["command"]
        args = server_def["args"]

        # Absolute path resolution for args if they look like files
        resolved_args = []
        for arg in args:
            if (PROJECT_ROOT / arg).exists():
                resolved_args.append(str(PROJECT_ROOT / arg))
            else:
                resolved_args.append(arg)

        server_config = {
            "command": cmd,
            "args": resolved_args,
            "env": env_vars
        }

        # Update local config
        config["mcpServers"][server_id] = server_config
        print("✅ Configured")
        updates_count += 1

    # Save updated config
    with open(MCP_CONFIG_PATH, "w") as f:
        json.dump(config, f, indent=2)

    print(f"\n✨ Bootstrap complete. {updates_count} servers configured in {MCP_CONFIG_PATH}")
    print("👉 You can now restart Claude Code/Desktop to use these tools.")

if __name__ == "__main__":
    bootstrap()
