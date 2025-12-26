#!/usr/bin/env python3
"""
Council Run - Unified Orchestrator for the Agent Council.
Chains: Task -> Smart Injection -> Swarm (Reflective Loop) -> (Execution) -> Wald -> Context
"""
import argparse
import asyncio
import json
import subprocess
import sys
import os
import re
import time
import shutil

sys.path.append(os.getcwd())

# Constants
SCRIPTS = {
    "swarm": "./scripts/dispatch_swarm.py",
    "wald": "./scripts/wald_score.py",
    "context": "./scripts/context_manager.py",
    "kb": "./scripts/knowledge_base.py",
}

MIN_SRC_PI = 0.80

def get_python_executable() -> str:
    venv_python = os.path.join(os.getcwd(), ".venv", "bin", "python")
    if os.path.isfile(venv_python) and os.access(venv_python, os.X_OK):
        return venv_python
    return sys.executable

def run_script(script: str, args: list, timeout_seconds: int = 120) -> dict:
    """Run a council script and capture output."""
    cmd = [get_python_executable(), script] + args
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout_seconds)
        return {
            "status": "success" if result.returncode == 0 else "failure",
            "stdout": result.stdout,
            "stderr": result.stderr,
            "code": result.returncode
        }
    except subprocess.TimeoutExpired:
        return {"status": "timeout", "stderr": "Script timed out", "code": -1}
    except Exception as e:
        return {"status": "error", "stderr": str(e), "code": -1}

def command_exists(cmd: str) -> bool:
    result = subprocess.run(
        ["bash", "-lc", f"command -v {cmd} >/dev/null 2>&1"],
        capture_output=True,
        text=True,
    )
    return result.returncode == 0

def run_verify() -> dict:
    verify_script = os.path.join("scripts", "verify.sh")
    if not os.path.exists(verify_script):
        return {"status": "missing", "stderr": f"{verify_script} not found", "code": 127}
    result = subprocess.run(
        ["bash", verify_script],
        capture_output=True,
        text=True,
    )
    return {
        "status": "success" if result.returncode == 0 else "failure",
        "stdout": result.stdout,
        "stderr": result.stderr,
        "code": result.returncode,
    }

def get_changed_files() -> list:
    """Return a list of changed files (staged or unstaged)."""
    result = subprocess.run(
        ["git", "status", "--porcelain"],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return []

    files = []
    for line in result.stdout.splitlines():
        if not line.strip():
            continue
        path = line[3:].strip()
        if " -> " in path:
            path = path.split(" -> ", 1)[1].strip()
        files.append(path)
    return files

def sync_spec_from_worktree(worktree_path: str) -> None:
    """Sync SPEC.md from a worktree into .council for downstream checks."""
    if not worktree_path:
        return
    src_spec = os.path.join(worktree_path, "SPEC.md")
    if not os.path.exists(src_spec):
        return
    os.makedirs(".council", exist_ok=True)
    shutil.copy2(src_spec, os.path.join(".council", "SPEC.md"))

def get_src_changes() -> list:
    """Filter changed files under src/."""
    return [path for path in get_changed_files() if path.startswith("src/")]

def get_diff_stat(paths: list) -> str:
    """Return a diff stat summary for selected paths."""
    if not paths:
        return ""
    result = subprocess.run(
        ["git", "diff", "--stat", "--"] + paths,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip() if result.returncode == 0 else ""

def build_src_vote_prompt(goal: str, src_changes: list, diff_stat: str) -> str:
    """Build a vote prompt for Council review."""
    files = "\n".join(f"- {path}" for path in src_changes)
    diff_block = diff_stat or "No diff stat available."
    return (
        "You are a Council reviewer. Evaluate whether the src/ changes should proceed.\n"
        "Return ONLY the following format:\n"
        "Vote: APPROVE | REJECT | HOLD\n"
        "Confidence: 0.0-1.0\n"
        "Rationale: <one paragraph>\n\n"
        f"Task Goal:\n{goal}\n\n"
        f"Changed src/ files:\n{files}\n\n"
        f"Diff summary:\n{diff_block}\n"
    )

def collect_cli_votes(prompt: str):
    """Collect votes using CLI tools when API keys are unavailable."""
    try:
        from council.mcp.ai_council_server import ModelResponse, ModelProvider
    except Exception:
        return [], ["council module unavailable for vote parsing"]

    env = os.environ.copy()
    if "CODEX_HOME" not in env:
        candidate = os.path.join(os.path.expanduser("~"), ".codex")
        os.makedirs(candidate, exist_ok=True)
        test_path = os.path.join(candidate, ".codex_write_test")
        try:
            with open(test_path, "w", encoding="utf-8") as handle:
                handle.write("ok")
            os.remove(test_path)
        except OSError:
            candidate = os.path.join(os.getcwd(), ".codex")
            os.makedirs(candidate, exist_ok=True)
        env["CODEX_HOME"] = candidate
        env["HOME"] = os.path.dirname(candidate)

    votes = []
    errors = []

    if command_exists("codex"):
        result = subprocess.run(
            ["codex", "exec", "--sandbox", "read-only", prompt],
            capture_output=True,
            text=True,
            env=env,
        )
        if result.returncode == 0 and result.stdout.strip():
            votes.append(
                ModelResponse(
                    provider=ModelProvider.OPENAI,
                    model_name="codex-cli",
                    content=result.stdout.strip(),
                    latency_ms=0,
                    success=True,
                )
            )
        else:
            errors.append(f"codex exec failed: {result.stderr.strip()}")

    if command_exists("gemini"):
        result = subprocess.run(
            ["gemini", "--prompt", "Return only Vote/Confidence/Rationale."],
            input=prompt,
            capture_output=True,
            text=True,
        )
        if result.returncode == 0 and result.stdout.strip():
            votes.append(
                ModelResponse(
                    provider=ModelProvider.GEMINI,
                    model_name="gemini-cli",
                    content=result.stdout.strip(),
                    latency_ms=0,
                    success=True,
                )
            )
        else:
            errors.append(f"gemini failed: {result.stderr.strip()}")

    return votes, errors

async def run_src_consensus(prompt: str):
    """Run Council consensus check for src/ changes."""
    try:
        from council.mcp.ai_council_server import AICouncilServer
    except Exception as exc:
        return None, f"Failed to import council server: {exc}"

    server = AICouncilServer()
    if server.get_enabled_models():
        responses = await server.query_parallel(prompt)
        if responses:
            result = server.evaluate_votes(responses)
            return result, None

    cli_responses, errors = collect_cli_votes(prompt)
    if not cli_responses:
        return None, "No enabled models or CLI tools available for Council vote."

    result = server.evaluate_votes(cli_responses)
    if errors:
        return result, "CLI fallback used; some models failed."
    return result, None

def extract_keywords(text: str) -> list:
    """Extract potential keywords from text (simple heuristic)."""
    # Remove common stop words and keep significant terms
    stop_words = {"the", "a", "an", "to", "in", "for", "of", "and", "with", "on", "at", "by", "from"}
    words = re.findall(r'\w+', text.lower())
    return [w for w in words if w not in stop_words and len(w) > 3]

def retrieve_lessons(goal: str) -> str:
    """Retrieve relevant lessons from Knowledge Base."""
    keywords = extract_keywords(goal)
    if not keywords:
        return ""
    
    print(f"🔍 Smart Injection: Searching lessons for keywords: {keywords}")
    
    lessons_found = []
    # Search for each keyword
    for kw in keywords[:3]: # Limit to top 3 keywords
        result = run_script(SCRIPTS["kb"], ["search", kw])
        if result["status"] == "success":
            # Parse output to extract lessons (simple text parsing for now)
            # In a real implementation, KB should return JSON
            if "Found" in result["stdout"]:
                lessons_found.append(result["stdout"].strip())
    
    if not lessons_found:
        return ""
        
    # Deduplicate and format
    unique_lessons = list(set(lessons_found))
    formatted_lessons = "\n".join(unique_lessons)
    
    return f"\n\n📚 RELEVANT LESSONS FROM PLAYBOOK:\n{formatted_lessons}\n"

def run_task(
    task: str,
    goal: str,
    risk: str,
    ephemeral: bool,
    learn: bool,
    dry_run: bool = False,
    swarm_pipeline: bool = False,
):
    """Execute a full council workflow."""
    print(f"🏛️ Council Run: {task}")
    print(f"   Goal: {goal}")
    print(f"   Risk: {risk.upper()}")
    if dry_run:
        print("   Mode: DRY RUN (Planning Only)")
    print("-" * 40)
    
    # 0. Smart Injection (Phase 1: Plan)
    print("\n[1/5] 🏗️ Phase 1: Plan & Research (Smart Injection)...")
    injected_context = retrieve_lessons(goal)
    if injected_context:
        print("   💉 Found relevant lessons. Augmenting goal.")
        goal += injected_context
    else:
        print("   ℹ️ No relevant lessons found.")

    if dry_run:
        print("\n✅ [DRY RUN] Planning complete. Context injected.")
        print("=" * 40)
        print(f"Augmented Goal:\n{goal}")
        return True

    # 1. Swarm Dispatch (Phase 2: Code)
    print("\n[2/5] 🛠️ Phase 2: Code & Execute (Swarm)...")
    
    max_retries = 3
    attempt = 0
    swarm_success = False
    
    while attempt < max_retries:
        attempt += 1
        print(f"   🔄 Attempt {attempt}/{max_retries}...")
        
        swarm_args = ["--task", task, "--goal", goal]
        if ephemeral:
            swarm_args.append("--ephemeral")
        if swarm_pipeline:
            swarm_args.append("--pipeline")
            
        swarm_timeout = 600 if swarm_pipeline else 120
        swarm_result = run_script(SCRIPTS["swarm"], swarm_args, timeout_seconds=swarm_timeout)
        
        if swarm_result["status"] == "success":
            print(swarm_result["stdout"])
            try:
                swarm_payload = json.loads(swarm_result["stdout"])
                sync_spec_from_worktree(swarm_payload.get("worktree", ""))
            except json.JSONDecodeError:
                pass
            swarm_success = True
            break
        else:
            error_preview = swarm_result["stderr"] or swarm_result["stdout"]
            preview = (error_preview or "")[:200]
            print(f"   ❌ Attempt {attempt} failed: {preview}...") # Truncate error
            
            # REFLECTIVE STEP: Update goal with error context
            error_context = f"\n\n[SYSTEM ERROR]: Previous attempt {attempt} failed with error:\n{swarm_result['stderr']}\n"
            
            # Call Facilitator for strategy
            print("   👔 Calling Facilitator for conflict resolution...")
            facilitator_result = run_script("./scripts/facilitator.py", ["--task", task, "--history", swarm_result['stderr']])
            
            if facilitator_result["status"] == "success":
                try:
                    fac_output = json.loads(facilitator_result["stdout"])
                    strategy = fac_output.get("strategy", "No strategy provided.")
                    print(f"   💡 Facilitator Strategy: {strategy}")
                    error_context += f"\n[FACILITATOR ADVICE]: {strategy}\n"
                except json.JSONDecodeError:
                    print("   ⚠️ Facilitator output parse failed.")
            
            error_context += "\nPLEASE ANALYZE THIS ERROR AND ADVICE TO ADJUST YOUR STRATEGY."
            goal += error_context
            
            if attempt < max_retries:
                print("   🧠 Reflecting and retrying in 2s...")
                time.sleep(2)
    
    if not swarm_success:
        print(f"❌ Swarm failed after {max_retries} attempts.")
        return False

    # 2.5 Council Gate for src/ changes
    src_changes = get_src_changes()
    if src_changes:
        print("\n[2.5/4] Council Gate: src/ changes detected.")
        diff_stat = get_diff_stat(src_changes)
        vote_prompt = build_src_vote_prompt(goal, src_changes, diff_stat)
        wald_result, error = asyncio.run(run_src_consensus(vote_prompt))
        if not wald_result:
            print(f"❌ Council vote unavailable: {error}")
            return False
        if error:
            print(f"   Warning: {error}")
        print(
            f"   Council pi={wald_result.pi_approve:.3f} "
            f"decision={wald_result.decision.value}"
        )
        if wald_result.pi_approve < MIN_SRC_PI:
            print(f"❌ Council consensus below {MIN_SRC_PI:.2f}. Manual review required.")
            return False
    
    # 3. Verification
    print("\n[3/5] 🧪 Phase 3: Verification (just verify)...")
    verify_result = run_verify()
    if verify_result["status"] != "success":
        print("❌ Verification failed.")
        if verify_result.get("stdout"):
            print(verify_result["stdout"])
        if verify_result.get("stderr"):
            print(verify_result["stderr"])
        return False

    # 4. Wald Score (Phase 4: Verify & Audit)
    print("\n[4/5] 🛡️ Phase 4: Verify & Audit (Wald Score)...")
    
    # 2.1 Adjudicator (Semantic Validation)
    print("   ⚖️ Running Adjudicator (Semantic Validation)...")
    # For now, we build the graph on the fly to ensure freshness
    run_script("./scripts/graph_builder.py", ["build"])
    # Validate the modified files (Mock: validating the task goal context conceptually)
    # In production, we would pass the specific files modified by the Swarm
    adj_result = run_script("./scripts/graph_builder.py", ["validate", "--file", "scripts/council_run.py"])
    
    if adj_result["status"] == "success":
        print(adj_result["stdout"])
    else:
        print(f"   ⚠️ Adjudicator Warning: {adj_result['stderr']}")

    # 2.2 Wald Score
    wald_result = run_script(SCRIPTS["wald"], ["--risk", risk])
    print(wald_result["stdout"])
    
    wald_passed = wald_result["code"] == 0
    
    # 5. Functional Codification (Phase 5: Consolidate & Learn)
    print("\n[5/5] 🧹 Phase 5: Consolidate & Learn...")
    if wald_passed:
        # 1. Compact Context
        context_result = run_script(SCRIPTS["context"], ["compact"])
        print(context_result["stdout"])
        
        # 2. Codify Routine (New)
        print("   ⚡ Codifying successful run...")
        codify_result = run_script("./scripts/codify_routine.py", ["--task", task, "--goal", goal, "--history", "success"])
        if codify_result["status"] == "success":
            print(f"   ✅ Routine generated: {json.loads(codify_result['stdout']).get('routine')}")
            
        # 3. Extract Lesson (Optional)
        if learn:
            print("   📚 Extracting Lesson...")
            kb_args = [
                "add",
                "--tags", f"task,{task}",
                "--problem", f"Goal: {goal[:50]}...",
                "--solution", f"Completed with risk={risk}"
            ]
            kb_result = run_script(SCRIPTS["kb"], kb_args)
            print(kb_result["stdout"])
    else:
        print("⚠️ Wald failed, skipping consolidation.")
    
    # Summary
    print("\n" + "=" * 40)
    if wald_passed:
        print("✅ Council Run Complete")
        return True
    else:
        print("⚠️ Council Run Requires Review")
        return False

def main():
    parser = argparse.ArgumentParser(description="Council Run - Unified Orchestrator")
    parser.add_argument("--task", required=True, help="Task ID")
    parser.add_argument("--goal", required=True, help="Goal description")
    parser.add_argument("--risk", choices=["low", "medium", "high"], default="medium", help="Risk level")
    parser.add_argument("--ephemeral", action="store_true", help="Cleanup worktree after execution")
    parser.add_argument("--learn", action="store_true", help="Extract lesson to knowledge base")
    parser.add_argument("--dry-run", action="store_true", help="Execute only planning phase (Smart Injection)")
    parser.add_argument("--swarm-pipeline", action="store_true", help="Run plan/audit/tdd/impl/verify in swarm")
    
    args = parser.parse_args()
    
    success = run_task(
        args.task,
        args.goal,
        args.risk,
        args.ephemeral,
        args.learn,
        args.dry_run,
        swarm_pipeline=args.swarm_pipeline,
    )
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
