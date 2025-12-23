#!/usr/bin/env python3
"""
Batch Executor - Execute tasks in Docker sandbox

Reads execution plan from YAML and runs tasks in order,
supporting file writes, commands, and validations.
"""

import argparse
import subprocess
import sys
import os
from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from pathlib import Path

try:
    import yaml
except ImportError:
    yaml = None


@dataclass
class Task:
    """A single execution task"""
    name: str
    task_type: str  # file_write, command, validation
    critical: bool = True
    content: Optional[str] = None  # For file_write
    path: Optional[str] = None  # For file_write
    cmd: Optional[str] = None  # For command


@dataclass
class ExecutionResult:
    """Result of task execution"""
    task_name: str
    success: bool
    output: str
    error: Optional[str] = None


class BatchExecutor:
    """
    Batch task executor for Docker sandbox
    
    Usage:
        executor = BatchExecutor()
        executor.load_plan("execution_plan.yaml")
        results = executor.run()
    """
    
    def __init__(self, working_dir: str = "."):
        """
        Initialize executor
        
        Args:
            working_dir: Working directory for execution
        """
        self.working_dir = working_dir
        self.tasks: List[Task] = []
        self.results: List[ExecutionResult] = []
    
    def load_plan(self, plan_path: str) -> int:
        """
        Load execution plan from YAML file
        
        Args:
            plan_path: Path to YAML plan file
            
        Returns:
            Number of tasks loaded
        """
        if yaml is None:
            raise ImportError("PyYAML required: pip install pyyaml")
        
        with open(plan_path, 'r') as f:
            plan = yaml.safe_load(f)
        
        self.tasks = []
        for task_data in plan.get("tasks", []):
            task = Task(
                name=task_data.get("name", "unnamed"),
                task_type=task_data.get("type", "command"),
                critical=task_data.get("critical", True),
                content=task_data.get("content"),
                path=task_data.get("path"),
                cmd=task_data.get("cmd"),
            )
            self.tasks.append(task)
        
        return len(self.tasks)
    
    def add_task(self, task: Task) -> None:
        """Add a task to the queue"""
        self.tasks.append(task)
    
    def _execute_file_write(self, task: Task) -> ExecutionResult:
        """Execute a file write task"""
        try:
            path = Path(self.working_dir) / task.path
            path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(path, 'w') as f:
                f.write(task.content or "")
            
            return ExecutionResult(
                task_name=task.name,
                success=True,
                output=f"Wrote {len(task.content or '')} bytes to {task.path}",
            )
        except Exception as e:
            return ExecutionResult(
                task_name=task.name,
                success=False,
                output="",
                error=str(e),
            )
    
    def _execute_command(self, task: Task) -> ExecutionResult:
        """Execute a command task"""
        try:
            result = subprocess.run(
                task.cmd,
                shell=True,
                cwd=self.working_dir,
                capture_output=True,
                text=True,
                timeout=300,
            )
            
            success = result.returncode == 0
            return ExecutionResult(
                task_name=task.name,
                success=success,
                output=result.stdout + result.stderr,
                error=None if success else f"Exit code: {result.returncode}",
            )
        except subprocess.TimeoutExpired:
            return ExecutionResult(
                task_name=task.name,
                success=False,
                output="",
                error="Command timed out",
            )
        except Exception as e:
            return ExecutionResult(
                task_name=task.name,
                success=False,
                output="",
                error=str(e),
            )
    
    def _execute_validation(self, task: Task) -> ExecutionResult:
        """Execute a validation task (just runs the command and checks exit code)"""
        return self._execute_command(task)
    
    def run(self, stop_on_critical_failure: bool = True) -> List[ExecutionResult]:
        """
        Execute all tasks in order
        
        Args:
            stop_on_critical_failure: Stop if a critical task fails
            
        Returns:
            List of execution results
        """
        self.results = []
        
        for task in self.tasks:
            print(f"[EXEC] {task.name}...", end=" ")
            
            if task.task_type == "file_write":
                result = self._execute_file_write(task)
            elif task.task_type == "command":
                result = self._execute_command(task)
            elif task.task_type == "validation":
                result = self._execute_validation(task)
            else:
                result = ExecutionResult(
                    task_name=task.name,
                    success=False,
                    output="",
                    error=f"Unknown task type: {task.task_type}",
                )
            
            self.results.append(result)
            
            if result.success:
                print("✓")
            else:
                print("✗")
                if task.critical and stop_on_critical_failure:
                    print(f"[ERROR] Critical task failed: {result.error}")
                    break
        
        return self.results
    
    def get_summary(self) -> Dict[str, Any]:
        """Get execution summary"""
        successful = sum(1 for r in self.results if r.success)
        failed = len(self.results) - successful
        
        return {
            "total": len(self.results),
            "successful": successful,
            "failed": failed,
            "success_rate": successful / len(self.results) if self.results else 0,
        }


def main():
    """CLI entry point"""
    parser = argparse.ArgumentParser(description="Batch executor for Docker sandbox")
    parser.add_argument("plan", help="Path to execution plan YAML")
    parser.add_argument("--working-dir", "-w", default=".", help="Working directory")
    parser.add_argument("--continue-on-error", "-c", action="store_true",
                       help="Continue on critical failures")
    
    args = parser.parse_args()
    
    executor = BatchExecutor(working_dir=args.working_dir)
    
    try:
        count = executor.load_plan(args.plan)
        print(f"Loaded {count} tasks from {args.plan}")
    except Exception as e:
        print(f"Error loading plan: {e}", file=sys.stderr)
        sys.exit(1)
    
    results = executor.run(stop_on_critical_failure=not args.continue_on_error)
    
    summary = executor.get_summary()
    print(f"\n{'='*40}")
    print(f"Execution Summary: {summary['successful']}/{summary['total']} passed")
    
    sys.exit(0 if summary['failed'] == 0 else 1)


if __name__ == "__main__":
    main()
