"""
Multi-Model Executor for Council Framework.

Enables parallel execution of multiple LLM models for different roles:
- Planner (Claude): Task decomposition and planning
- Executor (Gemini Flash): Fast code generation
- Reviewer (Codex): Code review and validation
- Expert (Gemini Pro): Complex problem solving

Based on 2026 best practices for multi-model orchestration.
"""

from __future__ import annotations

import asyncio
import time
import logging
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any, Callable
from enum import Enum

logger = logging.getLogger(__name__)


class ModelRole(Enum):
    """Roles for models in the multi-model pipeline."""

    PLANNER = "planner"  # Task decomposition, planning (Claude)
    EXECUTOR = "executor"  # Fast code generation (Gemini Flash)
    REVIEWER = "reviewer"  # Code review, validation (Codex)
    EXPERT = "expert"  # Complex problem solving (Gemini Pro)
    GENERAL = "general"  # General purpose


@dataclass
class ModelTask:
    """
    A task to be executed by a specific model.

    Attributes:
        model: Model identifier (e.g., "vertex_ai/gemini-2.0-flash")
        prompt: The prompt/messages to send
        role: The role this model plays in the pipeline
        timeout: Maximum execution time in seconds
        metadata: Additional context for the task
    """

    model: str
    prompt: str | List[Dict[str, str]]
    role: ModelRole = ModelRole.GENERAL
    timeout: float = 30.0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_messages(self) -> List[Dict[str, str]]:
        """Convert prompt to messages format."""
        if isinstance(self.prompt, str):
            return [{"role": "user", "content": self.prompt}]
        return self.prompt


@dataclass
class ModelResult:
    """
    Result from a model execution.

    Attributes:
        model: Model that produced this result
        role: Role of the model
        output: The model's response
        latency_ms: Execution time in milliseconds
        success: Whether execution succeeded
        error: Error message if failed
        token_usage: Token consumption details
    """

    model: str
    role: ModelRole
    output: str
    latency_ms: float
    success: bool
    error: Optional[str] = None
    token_usage: Dict[str, int] = field(default_factory=dict)

    @property
    def is_valid(self) -> bool:
        """Check if result is valid for downstream processing."""
        return self.success and bool(self.output.strip())


@dataclass
class ExecutionStats:
    """Statistics for multi-model execution."""

    total_tasks: int = 0
    successful: int = 0
    failed: int = 0
    total_latency_ms: float = 0.0
    total_tokens: int = 0

    @property
    def success_rate(self) -> float:
        """Calculate success rate."""
        if self.total_tasks == 0:
            return 0.0
        return self.successful / self.total_tasks

    @property
    def avg_latency_ms(self) -> float:
        """Calculate average latency."""
        if self.total_tasks == 0:
            return 0.0
        return self.total_latency_ms / self.total_tasks


class MultiModelExecutor:
    """
    Executes multiple model tasks in parallel.

    Supports:
    - Parallel execution with asyncio.gather
    - Per-task timeout handling
    - Automatic retry with fallback models
    - Execution statistics tracking
    - Result aggregation strategies

    Example:
        executor = MultiModelExecutor(llm_client)

        tasks = [
            ModelTask(model="claude-sonnet", prompt="Plan this task", role=ModelRole.PLANNER),
            ModelTask(model="gemini-flash", prompt="Generate code", role=ModelRole.EXECUTOR),
        ]

        results = await executor.execute_parallel(tasks)
    """

    def __init__(
        self,
        llm_client,
        max_concurrent: int = 5,
        default_timeout: float = 30.0,
        retry_count: int = 1,
    ):
        """
        Initialize the executor.

        Args:
            llm_client: LLMClient instance for making completions
            max_concurrent: Maximum concurrent model calls
            default_timeout: Default timeout for tasks
            retry_count: Number of retries on failure
        """
        self.llm_client = llm_client
        self.max_concurrent = max_concurrent
        self.default_timeout = default_timeout
        self.retry_count = retry_count
        self.stats = ExecutionStats()
        self._semaphore = asyncio.Semaphore(max_concurrent)

        # Fallback model mapping
        self.fallback_models: Dict[str, str] = {
            "vertex_ai/gemini-2.0-flash": "gpt-4o-mini",
            "claude-sonnet-4-20250514": "vertex_ai/gemini-2.0-flash",
            "gpt-5.2-codex": "claude-sonnet-4-20250514",
        }

    async def execute_parallel(
        self, tasks: List[ModelTask], aggregate: bool = False
    ) -> List[ModelResult]:
        """
        Execute multiple model tasks in parallel.

        Args:
            tasks: List of ModelTask to execute
            aggregate: If True, combine results from same role

        Returns:
            List of ModelResult, one per task
        """
        if not tasks:
            return []

        logger.info(f"Executing {len(tasks)} tasks in parallel")

        # Execute all tasks with semaphore limiting concurrency
        results = await asyncio.gather(
            *[self._execute_single(task) for task in tasks], return_exceptions=True
        )

        # Convert exceptions to failed results
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                processed_results.append(
                    ModelResult(
                        model=tasks[i].model,
                        role=tasks[i].role,
                        output="",
                        latency_ms=0.0,
                        success=False,
                        error=str(result),
                    )
                )
            else:
                processed_results.append(result)

        # Update stats
        self._update_stats(processed_results)

        return processed_results

    async def _execute_single(self, task: ModelTask) -> ModelResult:
        """Execute a single model task with timeout and retry."""
        async with self._semaphore:
            start_time = time.perf_counter()
            timeout = task.timeout or self.default_timeout

            for attempt in range(self.retry_count + 1):
                try:
                    output = await asyncio.wait_for(
                        self._call_llm(task), timeout=timeout
                    )

                    latency_ms = (time.perf_counter() - start_time) * 1000

                    logger.debug(
                        f"Task completed: model={task.model}, role={task.role.value}, "
                        f"latency={latency_ms:.0f}ms"
                    )

                    return ModelResult(
                        model=task.model,
                        role=task.role,
                        output=output,
                        latency_ms=latency_ms,
                        success=True,
                    )

                except asyncio.TimeoutError:
                    logger.warning(
                        f"Task timeout: model={task.model}, attempt={attempt + 1}"
                    )
                    if attempt < self.retry_count:
                        # Try fallback model
                        fallback = self.fallback_models.get(task.model)
                        if fallback:
                            logger.info(f"Falling back to {fallback}")
                            task = ModelTask(
                                model=fallback,
                                prompt=task.prompt,
                                role=task.role,
                                timeout=task.timeout,
                                metadata=task.metadata,
                            )
                        continue
                    return ModelResult(
                        model=task.model,
                        role=task.role,
                        output="",
                        latency_ms=(time.perf_counter() - start_time) * 1000,
                        success=False,
                        error="Timeout",
                    )

                except Exception as e:
                    logger.error(f"Task failed: model={task.model}, error={e}")
                    if attempt < self.retry_count:
                        continue
                    return ModelResult(
                        model=task.model,
                        role=task.role,
                        output="",
                        latency_ms=(time.perf_counter() - start_time) * 1000,
                        success=False,
                        error=str(e),
                    )

        # Should not reach here
        return ModelResult(
            model=task.model,
            role=task.role,
            output="",
            latency_ms=0.0,
            success=False,
            error="Unknown error",
        )

    async def _call_llm(self, task: ModelTask) -> str:
        """Call the LLM client."""
        messages = task.to_messages()

        # Use asyncio to wrap sync call if needed
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None,
            lambda: self.llm_client.completion(messages=messages, model=task.model),
        )
        return result

    def _update_stats(self, results: List[ModelResult]) -> None:
        """Update execution statistics."""
        for result in results:
            self.stats.total_tasks += 1
            if result.success:
                self.stats.successful += 1
            else:
                self.stats.failed += 1
            self.stats.total_latency_ms += result.latency_ms
            self.stats.total_tokens += sum(result.token_usage.values())

    async def execute_pipeline(
        self,
        planner_task: ModelTask,
        executor_tasks: List[ModelTask],
        reviewer_task: Optional[ModelTask] = None,
    ) -> Dict[str, ModelResult]:
        """
        Execute a standard Planner -> Executor -> Reviewer pipeline.

        Args:
            planner_task: Task for planning stage
            executor_tasks: Tasks for execution stage (can be parallel)
            reviewer_task: Optional task for review stage

        Returns:
            Dict mapping role to result
        """
        results = {}

        # 1. Planning stage
        logger.info("Pipeline: Planning stage")
        planner_results = await self.execute_parallel([planner_task])
        results["planner"] = planner_results[0]

        if not results["planner"].success:
            logger.error("Planning failed, aborting pipeline")
            return results

        # 2. Execution stage (parallel)
        logger.info(f"Pipeline: Execution stage ({len(executor_tasks)} tasks)")
        executor_results = await self.execute_parallel(executor_tasks)
        results["executors"] = executor_results

        # 3. Review stage (optional)
        if reviewer_task:
            logger.info("Pipeline: Review stage")
            reviewer_results = await self.execute_parallel([reviewer_task])
            results["reviewer"] = reviewer_results[0]

        return results

    def get_stats(self) -> ExecutionStats:
        """Get execution statistics."""
        return self.stats

    def reset_stats(self) -> None:
        """Reset execution statistics."""
        self.stats = ExecutionStats()


# Utility functions for common patterns
def create_planner_task(
    prompt: str, model: str = "claude-sonnet-4-20250514"
) -> ModelTask:
    """Create a planner task."""
    return ModelTask(
        model=model,
        prompt=prompt,
        role=ModelRole.PLANNER,
        timeout=60.0,  # Planners may need more time
    )


def create_executor_task(
    prompt: str, model: str = "vertex_ai/gemini-2.0-flash"
) -> ModelTask:
    """Create an executor task."""
    return ModelTask(
        model=model,
        prompt=prompt,
        role=ModelRole.EXECUTOR,
        timeout=30.0,
    )


def create_reviewer_task(prompt: str, model: str = "gpt-5.2-codex") -> ModelTask:
    """Create a reviewer task."""
    return ModelTask(
        model=model,
        prompt=prompt,
        role=ModelRole.REVIEWER,
        timeout=45.0,
    )


__all__ = [
    "ModelRole",
    "ModelTask",
    "ModelResult",
    "ExecutionStats",
    "MultiModelExecutor",
    "create_planner_task",
    "create_executor_task",
    "create_reviewer_task",
]
