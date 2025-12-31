"""
CoderAgent - 代码编写智能体
继承自 BaseAgent，通过 Hub 接收任务并发布代码产出。
"""

from dataclasses import dataclass, field
from typing import List
import logging

from council.agents.base import BaseAgent
from council.orchestration.events import Event, EventType


@dataclass
class CoderAgent(BaseAgent):
    """
    代码编写智能体

    职责:
    - 订阅 TASK_CREATED 事件
    - 接收任务后编写代码
    - 发布 CODE_WRITTEN 事件
    """

    capabilities: List[str] = field(default_factory=lambda: ["write_code", "refactor"])

    def __post_init__(self):
        """初始化时自动订阅任务事件"""
        self.logger = logging.getLogger(f"Agent.{self.name}")
        self.subscribe([EventType.TASK_CREATED])
        self.logger.info(f"CoderAgent '{self.name}' initialized and subscribed.")

    def handle_event(self, event: Event) -> None:
        """
        处理任务事件

        Args:
            event: 接收到的事件
        """
        if event.type == EventType.TASK_CREATED:
            self._handle_task(event)

    def _handle_task(self, event: Event) -> None:
        """
        处理任务创建事件

        Args:
            event: TASK_CREATED 事件
        """
        task = event.payload.get("task", "unknown")
        file_name = event.payload.get("file", "output.py")

        self.logger.info(f"CoderAgent received task: {task}")

        # 模拟代码编写 (实际实现中可调用 LLM)
        code_output = f"# Generated code for: {task}\n# File: {file_name}\npass"

        # 发布 CODE_WRITTEN 事件
        code_event = Event(
            type=EventType.CODE_WRITTEN,
            source=self.name,
            payload={
                "file": file_name,
                "task": task,
                "lines": len(code_output.splitlines()),
                "content": code_output,
            },
        )
        self.publish(code_event)
        self.logger.info(f"CoderAgent published CODE_WRITTEN for {file_name}")


__all__ = ["CoderAgent"]
