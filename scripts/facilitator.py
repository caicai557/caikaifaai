#!/usr/bin/env python3
"""
Facilitator AI - The Manager Layer.
Responsible for conflict resolution and strategy refinement when the Swarm fails.

In 2025 AGI best practices, the Facilitator uses LLM reasoning to:
1. Analyze error patterns
2. Suggest strategic pivots
3. Reduce semantic entropy in multi-agent discussions
"""

import argparse
import json
import subprocess
import sys


def command_exists(cmd: str) -> bool:
    """Check if a command exists in the system PATH."""
    result = subprocess.run(
        ["bash", "-lc", f"command -v {cmd} >/dev/null 2>&1"],
        capture_output=True,
    )
    return result.returncode == 0


def call_llm_cli(prompt: str) -> str | None:
    """
    Call an LLM CLI (Gemini or Claude) for intelligent conflict resolution.

    Priority:
    1. gemini CLI (if available)
    2. claude CLI (if available)
    3. None (fallback to heuristics)
    """
    system_prompt = (
        "You are a Facilitator AI in a multi-agent software development system. "
        "Analyze the error and provide a SINGLE actionable resolution strategy. "
        "Be concise (1-2 sentences). Focus on the root cause and concrete next step."
    )

    # Try Gemini CLI
    if command_exists("gemini"):
        try:
            result = subprocess.run(
                ["gemini", "--prompt", system_prompt],
                input=prompt,
                capture_output=True,
                text=True,
                timeout=30,
            )
            if result.returncode == 0 and result.stdout.strip():
                return result.stdout.strip()
        except Exception:
            pass

    # Try Claude CLI (if available in future)
    if command_exists("claude"):
        try:
            result = subprocess.run(
                ["claude", "-p", f"{system_prompt}\n\n{prompt}"],
                capture_output=True,
                text=True,
                timeout=30,
            )
            if result.returncode == 0 and result.stdout.strip():
                return result.stdout.strip()
        except Exception:
            pass

    return None


def heuristic_analysis(history: str) -> str:
    """Fallback heuristic analysis when LLM is not available."""
    if "ImportError" in history or "ModuleNotFoundError" in history:
        return "CRITICAL: Missing dependency detected. ACTION: Run 'pip install' or check 'requirements.txt'."
    elif "SyntaxError" in history:
        return "CRITICAL: Code syntax error. ACTION: Use 'python -m py_compile' to verify before running."
    elif "AssertionError" in history:
        return "CRITICAL: Test assumption failed. ACTION: Review test case against implementation logic."
    elif "Timeout" in history or "TimeoutError" in history:
        return "WARNING: Operation timed out. ACTION: Optimize query or increase timeout limit."
    elif "PermissionError" in history:
        return "CRITICAL: Permission denied. ACTION: Check file permissions or run with elevated privileges."
    elif "ConnectionError" in history or "ConnectionRefused" in history:
        return "WARNING: Network connection failed. ACTION: Check service availability or network configuration."
    else:
        return "ADVICE: The approach seems stuck. Try breaking the task into smaller sub-tasks."


def analyze_conflict(task_id: str, history: str) -> tuple[str, str]:
    """
    Analyze the execution history and generate a resolution strategy.

    Returns:
        tuple: (strategy, source) where source is 'llm' or 'heuristic'
    """
    print(f"👔 Facilitator: Analyzing conflict for task {task_id}...", file=sys.stderr)

<<<<<<< HEAD
    resolution = ""

    if "ImportError" in history:
        resolution = "CRITICAL: Missing dependency detected. ACTION: Run 'pip install' or check 'requirements.txt'."
    elif "SyntaxError" in history:
        resolution = "CRITICAL: Code syntax error. ACTION: Use 'python -m py_compile' to verify before running."
    elif "AssertionError" in history:
        resolution = "CRITICAL: Test assumption failed. ACTION: Review test case against implementation logic."
    elif "Timeout" in history:
        resolution = "WARNING: Operation timed out. ACTION: Optimize query or increase timeout limit."
    else:
        resolution = "ADVICE: The approach seems stuck. Try breaking the task into smaller sub-tasks."

    return resolution
=======
    # Try LLM first
    llm_prompt = f"Task ID: {task_id}\n\nError History:\n{history}\n\nProvide a resolution strategy:"
    llm_response = call_llm_cli(llm_prompt)

    if llm_response:
        print("   🤖 Using LLM-based analysis", file=sys.stderr)
        return llm_response, "llm"

    # Fallback to heuristics
    print("   📋 Using heuristic analysis (LLM unavailable)", file=sys.stderr)
    return heuristic_analysis(history), "heuristic"

>>>>>>> e2df45bcf4fae044c2ec81c7ea50a183bdc8bd86

def main():
    parser = argparse.ArgumentParser(description="Facilitator AI")
    parser.add_argument("--task", required=True, help="Task ID")
    parser.add_argument("--history", required=True, help="Execution history/Error logs")

    args = parser.parse_args()

<<<<<<< HEAD
    strategy = analyze_conflict(args.task, args.history)
=======
    strategy, source = analyze_conflict(args.task, args.history)
>>>>>>> e2df45bcf4fae044c2ec81c7ea50a183bdc8bd86

    result = {
        "task_id": args.task,
        "role": "Facilitator",
        "strategy": strategy,
        "source": source,
        "status": "resolved",
    }

    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
