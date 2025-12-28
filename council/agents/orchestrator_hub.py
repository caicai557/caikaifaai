"""
OrchestratorAgent - 编排智能体 (Supervisor Pattern)
继承自 BaseAgent，作为中央编排者管理其他智能体。
"""

from dataclasses import dataclass, field
from typing import List
import logging

from council.agents.base import BaseAgent
from council.orchestration.events import Event, EventType


@dataclass
class OrchestratorAgent(BaseAgent):
    """
    编排智能体 (Supervisor)

    职责:
    - 接收用户请求
    - 分发任务给专业智能体
    - 监控进度，计算 Wald Score
    - 决定: COMMIT / CONTINUE / STOP
    """

    capabilities: List[str] = field(
        default_factory=lambda: ["dispatch", "monitor", "decide"]
    )
    _success_count: int = field(default=0, repr=False)
    _failure_count: int = field(default=0, repr=False)

    def __post_init__(self):
        """初始化时订阅关键事件"""
        self.logger = logging.getLogger(f"Agent.{self.name}")
        self.subscribe([EventType.TEST_PASSED, EventType.TEST_FAILED])
        self.logger.info(f"OrchestratorAgent '{self.name}' initialized.")

    def handle_event(self, event: Event) -> None:
        """
        处理监控事件

        Args:
            event: 接收到的事件
        """
        if event.type == EventType.TEST_PASSED:
            self._success_count += 1
            self.logger.info(f"Test passed. Total: {self._success_count}")
        elif event.type == EventType.TEST_FAILED:
            self._failure_count += 1
            self.logger.warning(f"Test failed. Total: {self._failure_count}")

    def dispatch(self, task: str) -> None:
        """
        分发任务

        Args:
            task: 任务描述
        """
        self.logger.info(f"Dispatching task: {task}")
        task_event = Event(
            type=EventType.TASK_CREATED,
            source=self.name,
            payload={"task": task, "assigned_by": self.name},
        )
        self.publish(task_event)

    def get_wald_score(self) -> float:
        """
        计算 Wald Score (后验概率)

        Returns:
            π: 任务成功的后验概率 (0.0 - 1.0)
        """
        total = self._success_count + self._failure_count
        if total == 0:
            return 0.5  # 初始中性概率

        # 简单贝叶斯估计: π = successes / total
        pi = self._success_count / total
        return pi

    def should_commit(self, alpha: float = 0.95) -> bool:
        """
        判断是否应该提交

        Args:
            alpha: 置信上限 (默认 95%)

        Returns:
            True if π >= α
        """
        return self.get_wald_score() >= alpha

    def should_stop(self, beta: float = 0.05) -> bool:
        """
        判断是否应该停止

        Args:
            beta: 风险下限 (默认 5%)

        Returns:
            True if π <= β
        """
        return self.get_wald_score() <= beta


__all__ = ["OrchestratorAgent"]
