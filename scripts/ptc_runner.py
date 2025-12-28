#!/usr/bin/env python3
import argparse
import subprocess
import sys
import tempfile
import os
import json
from typing import Dict, Any

# Docker configuration
USE_DOCKER = os.environ.get("PTC_USE_DOCKER", "0") == "1"
DOCKER_IMAGE = os.environ.get("PTC_DOCKER_IMAGE", "cesi-ptc:latest")
PTC_OUTPUT_DIR = ".ptc_output"


def run_in_docker(script_content: str, timeout: int = 60) -> Dict[str, Any]:
    """
<<<<<<< HEAD
    Executes a Python script in a temporary isolated environment.

    Args:
        script_content: The Python code to execute.
        timeout: Execution timeout in seconds.

    Returns:
        Dict containing 'stdout', 'stderr', 'returncode', and 'status'.
=======
    Executes a Python script inside a Docker container for security isolation.

    Features:
    - Network isolation (--network none)
    - Read-only filesystem where possible
    - Limited resources
>>>>>>> e2df45bcf4fae044c2ec81c7ea50a183bdc8bd86
    """
    # Ensure output directory exists
    os.makedirs(PTC_OUTPUT_DIR, exist_ok=True)

    # Create script file in shared volume
    script_name = f"ptc_script_{os.getpid()}.py"
    script_path = os.path.join(PTC_OUTPUT_DIR, script_name)

    with open(script_path, "w") as f:
        f.write(script_content)

    try:
        abs_output_dir = os.path.abspath(PTC_OUTPUT_DIR)
        cmd = [
            "docker",
            "run",
            "--rm",
            "-v",
            f"{abs_output_dir}:/app:rw",
            "-w",
            "/app",
            "--network",
            "none",  # Network isolation
            "--memory",
            "256m",  # Memory limit
            "--cpus",
            "0.5",  # CPU limit
            DOCKER_IMAGE,
            "python",
            script_name,
        ]

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
        )

        return {
            "status": "success" if result.returncode == 0 else "failure",
            "stdout": result.stdout,
            "stderr": result.stderr,
            "returncode": result.returncode,
            "execution_mode": "docker",
        }

    except subprocess.TimeoutExpired:
        return {
            "status": "timeout",
            "stdout": "",
            "stderr": f"Docker execution timed out after {timeout} seconds.",
            "returncode": -1,
            "execution_mode": "docker",
        }
    except FileNotFoundError:
        return {
            "status": "error",
            "stdout": "",
            "stderr": "Docker not found. Install Docker or set PTC_USE_DOCKER=0.",
            "returncode": -1,
            "execution_mode": "docker",
        }
    except Exception as e:
        return {
            "status": "error",
            "stdout": "",
            "stderr": str(e),
            "returncode": -1,
            "execution_mode": "docker",
        }
    finally:
        # Cleanup
        if os.path.exists(script_path):
            os.remove(script_path)


def run_ptc_script(script_content: str, timeout: int = 60) -> Dict[str, Any]:
    """
    Executes a Python script in a temporary isolated environment.

    Args:
        script_content: The Python code to execute.
        timeout: Execution timeout in seconds.

    Returns:
        Dict containing 'stdout', 'stderr', 'returncode', and 'status'.
    """
    # Use Docker if enabled
    if USE_DOCKER:
        return run_in_docker(script_content, timeout)

    # Create a temporary file for the script
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".py", delete=False
    ) as temp_script:
        temp_script.write(script_content)
        temp_script_path = temp_script.name

    try:
        # Execute the script in a subprocess
        result = subprocess.run(
            [sys.executable, temp_script_path],
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=os.getcwd(),  # Run in current working directory to access files
            env={},  # Start with empty env for isolation (except what's needed)
        )

        return {
            "status": "success" if result.returncode == 0 else "failure",
            "stdout": result.stdout,
            "stderr": result.stderr,
            "returncode": result.returncode,
            "execution_mode": "subprocess",
        }

    except subprocess.TimeoutExpired:
        return {
            "status": "timeout",
            "stdout": "",
            "stderr": f"Execution timed out after {timeout} seconds.",
            "returncode": -1,
            "execution_mode": "subprocess",
        }
    except Exception as e:
        return {
            "status": "error",
            "stdout": "",
            "stderr": str(e),
            "returncode": -1,
            "execution_mode": "subprocess",
        }
    finally:
        # Cleanup
        if os.path.exists(temp_script_path):
            os.remove(temp_script_path)


def main():
    parser = argparse.ArgumentParser(
        description="PTC Runner (Sandboxed Python Executor)"
    )
    parser.add_argument("--script", help="Path to script file (optional)")
    parser.add_argument("--code", help="Inline Python code (optional)")
    parser.add_argument("--timeout", type=int, default=60, help="Timeout in seconds")

    args = parser.parse_args()

    code = ""
    if args.script:
        with open(args.script, "r") as f:
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
