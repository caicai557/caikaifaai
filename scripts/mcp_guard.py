#!/usr/bin/env python3
"""
MCP Guard - JSON-RPC Proxy with RBAC enforcement.
Intercepts tool calls and checks permissions before forwarding.
"""
import argparse
import json
import subprocess
import sys
import threading
import os
import signal

# Constants
PERMISSIONS_FILE = ".council/permissions.json"

def load_policy():
    """Load full policy including permissions and aliases."""
    if not os.path.exists(PERMISSIONS_FILE):
        return {"roles": {}, "tool_aliases": {}, "default_role": "claude"}
    
    try:
        with open(PERMISSIONS_FILE, 'r') as f:
            return json.load(f)
    except Exception:
        return {"roles": {}, "tool_aliases": {}, "default_role": "claude"}

def get_permissions(policy: dict, role: str) -> list:
    """Get allowed permissions for a role."""
    role_def = policy.get("roles", {}).get(role.lower())
    if not role_def:
        default_role = policy.get("default_role", "claude")
        role_def = policy.get("roles", {}).get(default_role)
    return role_def.get("permissions", []) if role_def else []

def resolve_tool_name(policy: dict, tool_name: str) -> str:
    """Resolve tool name through aliases."""
    aliases = policy.get("tool_aliases", {})
    return aliases.get(tool_name, tool_name)

def main():
    parser = argparse.ArgumentParser(description="MCP Guard (JSON-RPC Proxy)")
    parser.add_argument("--role", required=True, help="Agent Role (e.g., codex, claude)")
    parser.add_argument("--cmd", required=True, nargs=argparse.REMAINDER, help="Command to run")
    
    args = parser.parse_args()
    
    # 1. Load Policy
    policy = load_policy()
    allowed_permissions = get_permissions(policy, args.role)
    
    # 2. Start Subprocess
    cmd = args.cmd
    if cmd and cmd[0] == '--':
        cmd = cmd[1:]
        
    if not cmd:
        print(json.dumps({"jsonrpc": "2.0", "error": {"code": -32600, "message": "No command provided"}, "id": None}))
        sys.exit(1)

    proc = subprocess.Popen(
        cmd,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=sys.stderr,
        text=True,
        bufsize=1
    )

    # Graceful shutdown handler
    def shutdown(signum, frame):
        proc.terminate()
        sys.exit(0)
    
    signal.signal(signal.SIGTERM, shutdown)
    signal.signal(signal.SIGINT, shutdown)

    # 3. Input Handling (Stdin -> Subprocess)
    def handle_stdin():
        try:
            while True:
                line = sys.stdin.readline()
                if not line:  # EOF
                    proc.stdin.close()
                    break
                
                try:
                    request = json.loads(line)
                    
                    if request.get("method") == "tools/call":
                        tool_name = request.get("params", {}).get("name")
                        resolved_name = resolve_tool_name(policy, tool_name)
                        
                        # Always allow tool_search
                        if tool_name == "tool_search":
                            pass
                        elif resolved_name not in allowed_permissions:
                            error_response = {
                                "jsonrpc": "2.0",
                                "error": {
                                    "code": -32001,
                                    "message": f"Permission Denied: Role '{args.role}' cannot use tool '{tool_name}' (resolved: '{resolved_name}')."
                                },
                                "id": request.get("id")
                            }
                            print(json.dumps(error_response), flush=True)
                            continue
                    
                    proc.stdin.write(line)
                    proc.stdin.flush()
                    
                except json.JSONDecodeError:
                    proc.stdin.write(line)
                    proc.stdin.flush()
                except Exception as e:
                    print(f"MCP Guard Error: {e}", file=sys.stderr)
        except Exception:
            pass  # Stdin closed

    # 4. Output Handling (Subprocess -> Stdout)
    def handle_stdout():
        try:
            while True:
                line = proc.stdout.readline()
                if not line:
                    break
                print(line, end='', flush=True)
        except Exception:
            pass

    t_in = threading.Thread(target=handle_stdin, daemon=True)
    t_out = threading.Thread(target=handle_stdout, daemon=True)
    
    t_in.start()
    t_out.start()
    
    proc.wait()

if __name__ == "__main__":
    main()

