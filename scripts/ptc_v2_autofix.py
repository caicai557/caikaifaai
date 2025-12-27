#!/usr/bin/env python3
"""
PTC V2 - Self-Refining Execution Loop (自修正执行回路)

This is the "ultimate form" of PTC architecture. It upgrades the simple
"executor" into a "self-healing R&D closed loop".

In 2025 advanced engineering practice, this is called
"Self-Refining Execution Loop" (自修正执行回路).

Core Features:
- Context Stacking: Preserve conversation history across retries
- Error Reflection: Feed runtime errors back to the model for self-correction
- Circuit Breaker: MAX_RETRIES to prevent infinite loops (and burning API quota)

Usage:
    python scripts/ptc_v2_autofix.py "Calculate the average BTC price"
"""

import subprocess
import typer
import re
import os
import sys
import tempfile
from typing import Tuple

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

app = typer.Typer(help="PTC V2 Self-Refining Execution Loop")

# === Configuration Constants ===
MAX_RETRIES = 3  # Circuit breaker threshold
SANDBOX_TIMEOUT = 30  # Seconds
USE_DOCKER = os.environ.get("PTC_USE_DOCKER", "false").lower() == "true"

# Virtual SDK Documentation (injected into LLM context)
try:
    from scripts.ptc_sdk import VIRTUAL_SDK_DOCS
except ImportError:
    VIRTUAL_SDK_DOCS = """
LIBRARY: ptc_sdk
FUNCTIONS:
- fetch_market_data(symbol: str) -> List[Dict]
  Returns: [{"symbol": str, "price": float, "timestamp": str}, ...]
- save_result(filename: str, content: str) -> bool
- log_action(action: str, details: Dict = None) -> None
"""


# === 1. LLM Caller ===
def call_llm(history: str, use_real_llm: bool = False) -> str:
    """
    Call the LLM with the conversation history.

    In production, this would call Claude/Gemini/Codex API.
    For demo purposes, we use a mock with intentional bug on first attempt.

    Args:
        history: The full conversation history
        use_real_llm: If True, attempt to use real LLM APIs

    Returns:
        The LLM response containing code
    """
    # Count attempts from history
    attempt_count = history.count("[RUNTIME ERROR]") + 1

    print(f"\n🤖 [Model] Thinking (Iteration {attempt_count})...")

    if use_real_llm:
        return _call_real_llm(history)

    # === Mock LLM for Demo ===
    # First attempt: Intentionally write buggy code
    if "[RUNTIME ERROR]" not in history:
        return """
I will calculate the average price.
```python
import ptc_sdk

data = ptc_sdk.fetch_market_data("BTC")
# BUG: 'price' is not defined. It should be 'd["price"]'
avg = sum(price for d in data) / len(data)
print(f"Average: {avg}")
```
"""

    # Second attempt (after seeing error): Fix the code
    return """
I see the NameError. Let me fix the list comprehension to correctly access the dictionary key.
```python
import ptc_sdk

data = ptc_sdk.fetch_market_data("BTC")
# FIXED: Correctly accessing the dictionary key 'd["price"]'
avg = sum(d["price"] for d in data) / len(data)
print(f"Average BTC Price: {avg:.2f}")
```
"""


def _call_real_llm(history: str) -> str:
    """Attempt to call real LLM APIs (Gemini or Claude)."""

    # Try Gemini CLI
    if _command_exists("gemini"):
        try:
            result = subprocess.run(
                ["gemini"],
                input=history,
                capture_output=True,
                text=True,
                timeout=60,
            )
            if result.returncode == 0 and result.stdout.strip():
                return result.stdout.strip()
        except Exception:
            pass

    # Try Claude CLI
    if _command_exists("claude"):
        try:
            result = subprocess.run(
                ["claude", "-p", history],
                capture_output=True,
                text=True,
                timeout=60,
            )
            if result.returncode == 0 and result.stdout.strip():
                return result.stdout.strip()
        except Exception:
            pass

    # Fallback to mock
    print("⚠️  No LLM available, using mock response.")
    return call_llm(history, use_real_llm=False)


def _command_exists(cmd: str) -> bool:
    """Check if a command exists in PATH."""
    return subprocess.run(["which", cmd], capture_output=True).returncode == 0


# === 2. Code Extractor ===
def extract_code(text: str) -> str:
    """
    Extract Python code from markdown code blocks.

    Args:
        text: The LLM response text

    Returns:
        The extracted Python code, or empty string if not found
    """
    # Match ```python ... ``` blocks
    match = re.search(r"```python(.*?)```", text, re.DOTALL)
    if match:
        return match.group(1).strip()

    # Fallback: Match any ``` ... ``` blocks
    match = re.search(r"```(.*?)```", text, re.DOTALL)
    if match:
        return match.group(1).strip()

    return ""


# === 3. Sandbox Execution ===
def run_in_sandbox(script_content: str) -> Tuple[str, str]:
    """
    Execute Python script in an isolated sandbox.

    Args:
        script_content: The Python code to execute

    Returns:
        Tuple of (stdout, stderr)
    """
    if USE_DOCKER:
        return _run_in_docker(script_content)
    return _run_local_sandbox(script_content)


def _run_local_sandbox(script_content: str) -> Tuple[str, str]:
    """Run script in a local subprocess sandbox."""
    # Create temp file
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".py", delete=False, dir=os.getcwd()
    ) as f:
        f.write(script_content)
        temp_path = f.name

    try:
        # Add scripts directory to PYTHONPATH so ptc_sdk can be imported
        env = os.environ.copy()
        scripts_dir = os.path.join(os.getcwd(), "scripts")
        env["PYTHONPATH"] = f"{scripts_dir}:{env.get('PYTHONPATH', '')}"
        env["PTC_OUTPUT_DIR"] = os.path.join(os.getcwd(), ".ptc_output")

        os.makedirs(env["PTC_OUTPUT_DIR"], exist_ok=True)

        result = subprocess.run(
            [sys.executable, temp_path],
            capture_output=True,
            text=True,
            timeout=SANDBOX_TIMEOUT,
            env=env,
            cwd=os.getcwd(),
        )
        return result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return "", f"Execution timed out after {SANDBOX_TIMEOUT} seconds."
    except Exception as e:
        return "", str(e)
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)


def _run_in_docker(script_content: str) -> Tuple[str, str]:
    """Run script in Docker sandbox container."""
    temp_path = os.path.join(os.getcwd(), "temp_agent_script.py")

    try:
        with open(temp_path, "w") as f:
            f.write(script_content)

        result = subprocess.run(
            [
                "docker",
                "run",
                "--rm",
                "-v",
                f"{temp_path}:/sandbox/agent_script.py:ro",
                "ptc-runner",
            ],
            capture_output=True,
            text=True,
            timeout=SANDBOX_TIMEOUT,
        )
        return result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return "", f"Docker execution timed out after {SANDBOX_TIMEOUT} seconds."
    except Exception as e:
        return "", str(e)
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)


# === 4. Self-Healing Main Logic (The Healing Loop) ===
@app.command()
def execute(
    task: str = typer.Argument(..., help="The task to execute"),
    use_real_llm: bool = typer.Option(False, "--real-llm", help="Use real LLM APIs"),
    docker: bool = typer.Option(False, "--docker", help="Use Docker sandbox"),
):
    """
    Execute a task with self-healing capability.

    The engine will:
    1. Generate code from the task description
    2. Run the code in a sandbox
    3. If it fails, feed the error back to the LLM
    4. Retry until success or MAX_RETRIES reached
    """
    global USE_DOCKER
    USE_DOCKER = docker

    print(f"🚀 [V2 Engine] Task: {task}")
    print(f"   Max Retries: {MAX_RETRIES}")
    print(f"   Sandbox: {'Docker' if USE_DOCKER else 'Local subprocess'}")
    print("-" * 50)

    # Initialize context (Context Stacking)
    history = f"""SYSTEM: You are a code generator. Use the following SDK.

{VIRTUAL_SDK_DOCS}

Generate Python code that accomplishes the user's task.
Wrap your code in ```python ... ``` blocks.

USER TASK: {task}

Generate a complete Python script:"""

    attempt = 0

    while attempt < MAX_RETRIES:
        attempt += 1

        # A. Generate Code
        response = call_llm(history, use_real_llm)
        code = extract_code(response)

        if not code:
            print("❌ No code detected in response. Terminating.")
            break

        print(f"📜 [Attempt {attempt}] Code generated, sending to sandbox...")

        # B. Execute Code
        stdout, stderr = run_in_sandbox(code)

        # C. Judgment
        if not stderr:
            # === SUCCESS PATH ===
            print("\n✅ [SUCCESS] Execution completed!")
            print(f"📤 Output:\n{stdout}")
            print(f"🎉 Task completed in {attempt} attempt(s).")
            return

        else:
            # === FAILURE PATH (Trigger Self-Healing) ===
            print(f"\n⚠️  [FAILURE] Attempt {attempt} failed!")
            print(f"🔍 Error: {stderr.strip()[:200]}...")

            if attempt < MAX_RETRIES:
                print("🚑 Initiating Auto-Fix Loop (Error Reflection)...")

                # D. Construct Fix Prompt (Error Reflection - feed error back to AI)
                history += f"""

ASSISTANT CODE:
```python
{code}
```

[RUNTIME ERROR]:
{stderr}

SYSTEM: The code failed. Analyze the error and rewrite the COMPLETE script to fix it.
Do not explain, just output the corrected code in ```python ... ``` blocks."""

            else:
                print("💀 Maximum retries reached. Task failed.")
                print("\n📋 Final Error:")
                print(stderr)


@app.command()
def demo():
    """
    Run a demo that shows the self-healing loop in action.

    The demo intentionally generates buggy code on the first attempt,
    then automatically fixes it on the second attempt.
    """
    print("=" * 60)
    print("🎬 PTC V2 Self-Refining Execution Loop DEMO")
    print("=" * 60)
    print()
    print("This demo will:")
    print("  1. Generate code with an intentional bug (NameError)")
    print("  2. Capture the error and feed it back to the model")
    print("  3. Automatically fix the code and re-run")
    print()

    execute("Calculate the average BTC price", use_real_llm=False, docker=False)


if __name__ == "__main__":
    app()
