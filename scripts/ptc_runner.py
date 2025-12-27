#!/usr/bin/env python3
import argparse
import subprocess
import sys
import tempfile
import os
import json
from typing import Dict, Any

def run_ptc_script(script_content: str, timeout: int = 60) -> Dict[str, Any]:
    """
    Executes a Python script in a temporary isolated environment.

    Args:
        script_content: The Python code to execute.
        timeout: Execution timeout in seconds.

    Returns:
        Dict containing 'stdout', 'stderr', 'returncode', and 'status'.
    """
    # Create a temporary file for the script
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as temp_script:
        temp_script.write(script_content)
        temp_script_path = temp_script.name

    try:
        # Execute the script in a subprocess
        # In a future version, this could use 'docker run' for stronger isolation
        result = subprocess.run(
            [sys.executable, temp_script_path],
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=os.getcwd(), # Run in current working directory to access files
            env={} # Start with empty env for isolation (except what's needed)
        )

        return {
            "status": "success" if result.returncode == 0 else "failure",
            "stdout": result.stdout,
            "stderr": result.stderr,
            "returncode": result.returncode
        }

    except subprocess.TimeoutExpired:
        return {
            "status": "timeout",
            "stdout": "",
            "stderr": f"Execution timed out after {timeout} seconds.",
            "returncode": -1
        }
    except Exception as e:
        return {
            "status": "error",
            "stdout": "",
            "stderr": str(e),
            "returncode": -1
        }
    finally:
        # Cleanup
        if os.path.exists(temp_script_path):
            os.remove(temp_script_path)

def main():
    parser = argparse.ArgumentParser(description="PTC Runner (Sandboxed Python Executor)")
    parser.add_argument("--script", help="Path to script file (optional)")
    parser.add_argument("--code", help="Inline Python code (optional)")
    parser.add_argument("--timeout", type=int, default=60, help="Timeout in seconds")

    args = parser.parse_args()

    code = ""
    if args.script:
        with open(args.script, 'r') as f:
            code = f.read()
    elif args.code:
        code = args.code
    else:
        # Read from stdin
        code = sys.stdin.read()

    if not code:
        print(json.dumps({"status": "error", "stderr": "No code provided"}))
        sys.exit(1)

    result = run_ptc_script(code, args.timeout)
    print(json.dumps(result, indent=2))

    if result["status"] != "success":
        sys.exit(result["returncode"] if result["returncode"] != 0 else 1)

if __name__ == "__main__":
    main()
