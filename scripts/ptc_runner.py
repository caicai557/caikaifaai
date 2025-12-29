#!/usr/bin/env python3
import argparse
import sys
import os
import json
from typing import Dict, Any, Optional

from council.sandbox import get_sandbox_runner

# Docker configuration
USE_DOCKER = os.environ.get("PTC_USE_DOCKER", "0") == "1"
DOCKER_IMAGE = os.environ.get("PTC_DOCKER_IMAGE", "cesi-ptc:latest")
PTC_OUTPUT_DIR = ".ptc_output"
SANDBOX_PROVIDER = os.environ.get("PTC_SANDBOX_PROVIDER")


def _resolve_provider() -> str:
    if SANDBOX_PROVIDER:
        return SANDBOX_PROVIDER
    return "docker" if USE_DOCKER else "local"


def _build_local_env(output_dir: str) -> Dict[str, str]:
    env = os.environ.copy()
    scripts_dir = os.path.join(os.getcwd(), "scripts")
    env["PYTHONPATH"] = f"{scripts_dir}:{env.get('PYTHONPATH', '')}"
    env["PTC_OUTPUT_DIR"] = os.path.join(os.getcwd(), output_dir)
    os.makedirs(env["PTC_OUTPUT_DIR"], exist_ok=True)
    return env


def run_ptc_script(script_content: str, timeout: int = 60) -> Dict[str, Any]:
    """
    Executes a Python script in a temporary isolated environment.

    Args:
        script_content: The Python code to execute.
        timeout: Execution timeout in seconds.

    Returns:
        Dict containing 'stdout', 'stderr', 'returncode', and 'status'.
    """
    provider = _resolve_provider()
    env: Optional[Dict[str, str]] = None
    if provider == "local":
        env = _build_local_env(PTC_OUTPUT_DIR)

    runner = get_sandbox_runner(
        provider,
        docker_image=DOCKER_IMAGE,
        output_dir=PTC_OUTPUT_DIR,
        env=env,
        working_dir=os.getcwd(),
        e2b_api_key=os.environ.get("E2B_API_KEY"),
        e2b_template=os.environ.get("E2B_TEMPLATE", "python"),
    )
    result = runner.run(script_content, timeout=timeout)
    return result.to_dict()


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
