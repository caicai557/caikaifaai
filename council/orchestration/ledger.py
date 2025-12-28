"""
Ledger Module - 双账本状态管理系统

实现 2025 AGI 编排层最佳实践中的 Task Ledger 和 Progress Ledger。

Task Ledger:
- 已知事实 (known_facts)
- 待查信息 (pending_queries)
- 待推导结论 (pending_conclusions)
- 初始执行计划 (initial_plan)

Progress Ledger:
- 迭代记录
- 停滞计数器 (stagnation_counter)
- 5个核心问题自我反思
"""

from dataclasses import dataclass, field
from typing import Dict, List, Any
from datetime import datetime
from enum import Enum


class IterationStatus(Enum):
    """迭代状态"""

    PROGRESS = "progress"  # 有实质进展
    STAGNANT = "stagnant"  # 停滞
    BLOCKED = "blocked"  # 被阻塞
    COMPLETED = "completed"  # 完成


@dataclass
class TaskLedger:
    """
    任务账本 - 记录任务的静态和动态状态

    Usage:
        ledger = TaskLedger(task_id="IMPL-001", goal="实现用户登录")
        ledger.add_fact("framework", "FastAPI")
        ledger.add_query("需要查询现有认证方案")
        ledger.set_plan(["TDD", "Impl", "Verify"])
    """

    task_id: str
    goal: str
    known_facts: Dict[str, Any] = field(default_factory=dict)
    pending_queries: List[str] = field(default_factory=list)
    pending_conclusions: List[str] = field(default_factory=list)
    initial_plan: List[str] = field(default_factory=list)
    experience_hints: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)

    def add_fact(self, key: str, value: Any) -> None:
        """添加已知事实"""
        self.known_facts[key] = value

    def add_query(self, query: str) -> None:
        """添加待查信息"""
        if query not in self.pending_queries:
            self.pending_queries.append(query)

    def resolve_query(self, query: str, result: Any) -> None:
        """解决待查信息并转为已知事实"""
        if query in self.pending_queries:
            self.pending_queries.remove(query)
            self.add_fact(f"resolved:{query[:30]}", result)

    def add_conclusion(self, conclusion: str) -> None:
        """添加待推导结论"""
        if conclusion not in self.pending_conclusions:
            self.pending_conclusions.append(conclusion)

    def set_plan(self, steps: List[str]) -> None:
        """设置初始执行计划"""
        self.initial_plan = steps

    def add_hint(self, hint: str) -> None:
        """添加经验猜测 (利用模型内部知识库)"""
        if hint not in self.experience_hints:
            self.experience_hints.append(hint)

    def to_context(self) -> str:
        """转换为 LLM 可用的上下文字符串"""
        lines = [
            f"=== TASK LEDGER: {self.task_id} ===",
            f"Goal: {self.goal}",
            "",
            "Known Facts:",
        ]
        for k, v in self.known_facts.items():
            lines.append(f"  - {k}: {v}")

        if self.pending_queries:
            lines.append("\nPending Queries:")
            for q in self.pending_queries:
                lines.append(f"  - {q}")

        if self.initial_plan:
            lines.append("\nExecution Plan:")
            for i, step in enumerate(self.initial_plan, 1):
                lines.append(f"  {i}. {step}")

        if self.experience_hints:
            lines.append("\nExperience Hints:")
            for h in self.experience_hints:
                lines.append(f"  - {h}")

        return "\n".join(lines)


@dataclass
class IterationRecord:
    """迭代记录"""

    iteration: int
    status: IterationStatus
    action: str
    result: str
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class ProgressLedger:
    """
    进度账本 - 实时追踪执行进度

    Features:
    - 记录每次迭代
    - 停滞计数器 (stagnation_counter)
    - 5个核心问题自我反思
    - 自动重规划触发

    Usage:
        ledger = ProgressLedger(max_stagnation=3)
        ledger.record_iteration(progress=True, action="TDD", result="生成了5个测试")
        ledger.record_iteration(progress=False, action="Impl", result="编译失败")

        if ledger.should_replan():
            # 触发重规划
            ledger.reset_stagnation()
    """

    max_stagnation: int = 3
    iterations: List[IterationRecord] = field(default_factory=list)
    stagnation_count: int = 0
    is_completed: bool = False

    def record_iteration(
        self,
        progress: bool,
        action: str = "",
        result: str = "",
    ) -> IterationStatus:
        """
        记录一次迭代

        Args:
            progress: 是否有实质进展
            action: 执行的动作
            result: 执行结果

        Returns:
            本次迭代状态
        """
        iteration_num = len(self.iterations) + 1

        if progress:
            status = IterationStatus.PROGRESS
            self.stagnation_count = 0  # 重置停滞计数
        else:
            status = IterationStatus.STAGNANT
            self.stagnation_count += 1

        record = IterationRecord(
            iteration=iteration_num,
            status=status,
            action=action,
            result=result,
        )
        self.iterations.append(record)

        return status

    def should_replan(self) -> bool:
        """检查是否应该触发重规划"""
        return self.stagnation_count >= self.max_stagnation

    def reset_stagnation(self) -> None:
        """重置停滞计数器 (重规划后调用)"""
        self.stagnation_count = 0

    def mark_completed(self) -> None:
        """标记任务完成"""
        self.is_completed = True

    def reflect(self) -> Dict[str, Any]:
        """
        5个核心问题自我反思

        Returns:
            Dict with answers to 5 core questions
        """
        return {
            "task_completed": self.is_completed,
            "in_loop": self._detect_loop(),
            "stagnant": self.stagnation_count > 0,
            "stagnation_count": self.stagnation_count,
            "should_replan": self.should_replan(),
            "total_iterations": len(self.iterations),
            "last_action": self.iterations[-1].action if self.iterations else None,
        }

    def _detect_loop(self) -> bool:
        """检测是否存在死循环 (相同错误连续出现)"""
        if len(self.iterations) < 3:
            return False

        # 检查最近3次迭代是否结果相同
        recent = self.iterations[-3:]
        results = [r.result for r in recent]
        return len(set(results)) == 1 and all(
            r.status == IterationStatus.STAGNANT for r in recent
        )

    def get_summary(self) -> str:
        """获取进度摘要"""
        reflection = self.reflect()
        lines = [
            "=== PROGRESS LEDGER ===",
            f"Total Iterations: {reflection['total_iterations']}",
            f"Stagnation Count: {reflection['stagnation_count']} / {self.max_stagnation}",
            f"In Loop: {reflection['in_loop']}",
            f"Should Replan: {reflection['should_replan']}",
            f"Completed: {reflection['task_completed']}",
        ]

        if self.iterations:
            lines.append("\nRecent Iterations:")
            for record in self.iterations[-5:]:
                lines.append(
                    f"  [{record.iteration}] {record.status.value}: "
                    f"{record.action} -> {record.result[:50]}..."
                )

        return "\n".join(lines)


@dataclass
class DualLedger:
    """
    双账本系统 - 统一封装

    Combines TaskLedger and ProgressLedger for complete state management.
    """

    task: TaskLedger
    progress: ProgressLedger

    @classmethod
    def create(
        cls,
        task_id: str,
        goal: str,
        max_stagnation: int = 3,
    ) -> "DualLedger":
        """
        创建双账本实例

        Args:
            task_id: 任务ID
            goal: 任务目标
            max_stagnation: 最大停滞次数

        Returns:
            DualLedger instance
        """
        return cls(
            task=TaskLedger(task_id=task_id, goal=goal),
            progress=ProgressLedger(max_stagnation=max_stagnation),
        )

    def get_full_context(self) -> str:
        """获取完整上下文"""
        return f"{self.task.to_context()}\n\n{self.progress.get_summary()}"


# 导出
__all__ = [
    "TaskLedger",
    "ProgressLedger",
    "DualLedger",
    "IterationRecord",
    "IterationStatus",
]
