"""
PlannerAgent - 规划智能体
继承自 BaseAgent，负责将目标分解为子任务。
"""

from dataclasses import dataclass, field
from typing import List
import logging

from council.agents.base import BaseAgent
from council.orchestration.events import Event, EventType


@dataclass
class PlannerAgent(BaseAgent):
    """
    规划智能体

    职责:
    - 接收高层目标
    - 分解为可执行的子任务
    - 发布 TASK_CREATED 事件
    """

    capabilities: List[str] = field(
        default_factory=lambda: ["decompose_goal", "prioritize"]
    )

    def __post_init__(self):
        """初始化"""
        self.logger = logging.getLogger(f"Agent.{self.name}")
        self.logger.info(f"PlannerAgent '{self.name}' initialized.")

    def handle_event(self, event: Event) -> None:
        """PlannerAgent 通常不订阅事件，而是被直接调用"""
        pass

    def decompose(self, goal: str) -> List[str]:
        """
        将目标分解为子任务列表

        Args:
            goal: 高层目标描述

        Returns:
            子任务列表
        """
        # 模拟分解 (实际实现中可调用 LLM)
        subtasks = [
            f"Research: {goal}",
            f"Design: {goal}",
            f"Implement: {goal}",
            f"Test: {goal}",
            f"Document: {goal}",
        ]
        self.logger.info(f"Decomposed goal into {len(subtasks)} subtasks")
        return subtasks

    def plan_and_publish(self, goal: str) -> None:
        """
        分解目标并发布任务事件

        Args:
            goal: 高层目标描述
        """
        subtasks = self.decompose(goal)

        for i, task in enumerate(subtasks):
            task_event = Event(
                type=EventType.TASK_CREATED,
                source=self.name,
                payload={
                    "task": task,
                    "priority": i + 1,
                    "parent_goal": goal,
                },
            )
            self.publish(task_event)

        self.logger.info(f"Published {len(subtasks)} TASK_CREATED events")


__all__ = ["PlannerAgent"]
