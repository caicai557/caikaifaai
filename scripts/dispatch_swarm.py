#!/usr/bin/env python3
import argparse
import subprocess
import os
import sys
import json
import shutil
from typing import List, Dict, Any

WORKTREE_MANAGER = "./scripts/worktree_manager.sh"
SYNC_SCRIPTS = [
    "codemap.sh",
    "audit_gemini.sh",
    "tdd_gemini.sh",
    "impl_gemini.sh",
    "verify.sh",
]


def run_command(cmd: List[str], cwd: str = ".") -> bool:
    try:
        subprocess.run(cmd, cwd=cwd, check=True, capture_output=True, text=True)
        return True
    except subprocess.CalledProcessError:
        return False


def run_step(cmd: List[str], cwd: str) -> Dict[str, Any]:
    try:
        result = subprocess.run(
            cmd, cwd=cwd, check=True, capture_output=True, text=True
        )
        return {"ok": True, "stdout": result.stdout, "stderr": result.stderr}
    except subprocess.CalledProcessError as exc:
        return {
            "ok": False,
            "stdout": exc.stdout,
            "stderr": exc.stderr,
            "code": exc.returncode,
        }


def sync_worktree_scripts(worktree_path: str) -> None:
    """Copy updated pipeline scripts into the worktree."""
    root = os.getcwd()
    src_dir = os.path.join(root, "scripts")
    dst_dir = os.path.join(worktree_path, "scripts")
    os.makedirs(dst_dir, exist_ok=True)
    for name in SYNC_SCRIPTS:
        src = os.path.join(src_dir, name)
        dst = os.path.join(dst_dir, name)
        if os.path.exists(src):
            shutil.copy2(src, dst)
            os.chmod(dst, 0o755)


def dispatch_agent_tool(
    task_id: str,
    goal: str,
    ephemeral: bool = False,
    run_pipeline: bool = False,
    run_plan: bool = False,
    run_audit: bool = False,
    run_tdd: bool = False,
    run_impl: bool = False,
    run_verify: bool = False,
) -> Dict[str, Any]:
    """
    Spawns an ephemeral agent in a worktree to achieve a goal.
    Returns a JSON result object.
    """
    branch_name = f"swarm/{task_id}"
    worktree_path = f"../cesi.worktrees/{branch_name}"

    print(f"🚀 [Agent-as-a-Tool] Spawning {task_id} (Ephemeral: {ephemeral})...")

    # 1. Create Clean Room (Worktree)
    if not run_command([WORKTREE_MANAGER, "create", branch_name]):
        return {"status": "error", "message": "Failed to create worktree"}

    # 2. Inject Context (Goal)
    try:
        with open(f"{worktree_path}/GOAL.md", "w") as f:
            f.write(f"# Goal for {task_id}\n{goal}")

        sync_worktree_scripts(worktree_path)

        # 3. Execute (Optional Pipeline)
        steps = []
        if run_pipeline or run_plan:
            steps.append(["bash", "scripts/codemap.sh"])
            print(
                "⚠️  Plan step skipped: Please run /plan interactively in Claude Code (Claude Opus 4.5)"
            )
        if run_pipeline or run_audit:
            steps.append(["bash", "scripts/audit_gemini.sh"])
        if run_pipeline or run_tdd:
            steps.append(["bash", "scripts/tdd_gemini.sh"])
        if run_pipeline or run_impl:
            steps.append(["bash", "scripts/impl_gemini.sh"])
        if run_pipeline or run_verify:
            steps.append(["bash", "scripts/verify.sh"])
        if run_impl and not (run_pipeline or run_verify):
            steps.append(["bash", "scripts/verify.sh"])

        step_results = []
        for cmd in steps:
            result = run_step(cmd, cwd=worktree_path)
            step_results.append({"cmd": cmd, **result})
            if not result["ok"]:
                return {
                    "task_id": task_id,
                    "status": "error",
                    "worktree": worktree_path,
                    "summary": f"Step failed: {' '.join(cmd)}",
                    "steps": step_results,
                }

        # 4. Summary
        result = {
            "task_id": task_id,
            "status": "success",
            "worktree": worktree_path,
            "artifacts": ["GOAL.md"],
            "summary": f"Agent initialized environment for: {goal}",
            "steps": step_results,
        }

        # 5. Cleanup (Transient Context)
        if ephemeral:
            print(f"🧹 Cleaning up ephemeral worktree {branch_name}...")
            # Use 'git worktree remove --force' to ensure cleanup even if there are changes
            if run_command([WORKTREE_MANAGER, "remove", branch_name]):
                result["worktree"] = "cleaned_up"
                result["status"] = "success_ephemeral"
            else:
<<<<<<< HEAD
                 # Fallback to manual removal if script fails
                 try:
                     shutil.rmtree(worktree_path)
                     run_command(["git", "worktree", "prune"])
                     result["worktree"] = "cleaned_up_forced"
                     result["status"] = "success_ephemeral_forced"
                 except Exception as e:
                     result["cleanup_error"] = f"Failed to remove worktree: {str(e)}"
=======
                # Fallback to manual removal if script fails
                try:
                    shutil.rmtree(worktree_path)
                    run_command(["git", "worktree", "prune"])
                    result["worktree"] = "cleaned_up_forced"
                    result["status"] = "success_ephemeral_forced"
                except Exception as e:
                    result["cleanup_error"] = f"Failed to remove worktree: {str(e)}"
>>>>>>> e2df45bcf4fae044c2ec81c7ea50a183bdc8bd86

        return result

    except Exception as e:
        return {"status": "error", "message": str(e)}


def main():
    parser = argparse.ArgumentParser(description="Swarm Dispatch (Agent-as-a-Tool)")
    parser.add_argument("--task", required=True, help="Task ID")
    parser.add_argument("--goal", required=True, help="Goal description")
    parser.add_argument(
        "--ephemeral", action="store_true", help="Cleanup worktree after execution"
    )
    parser.add_argument(
        "--pipeline",
        action="store_true",
        help="Run plan/audit/tdd/impl/verify pipeline",
    )
    parser.add_argument(
        "--plan", action="store_true", help="Run plan step (codemap + plan)"
    )
    parser.add_argument("--audit", action="store_true", help="Run audit step")
    parser.add_argument("--tdd", action="store_true", help="Run TDD step")
    parser.add_argument("--impl", action="store_true", help="Run implementation step")
    parser.add_argument("--verify", action="store_true", help="Run verify step")

    args = parser.parse_args()

    result = dispatch_agent_tool(
        args.task,
        args.goal,
        args.ephemeral,
        run_pipeline=args.pipeline,
        run_plan=args.plan,
        run_audit=args.audit,
        run_tdd=args.tdd,
        run_impl=args.impl,
        run_verify=args.verify,
    )
    print(json.dumps(result, indent=2))
    status = result.get("status", "")
    sys.exit(0 if status.startswith("success") else 1)


if __name__ == "__main__":
    main()
