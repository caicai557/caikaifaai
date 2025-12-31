"""
QAAgent - 质量保证智能体
继承自 BaseAgent，通过 Hub 订阅代码事件并运行测试。
"""

from dataclasses import dataclass, field
from typing import List
import logging

from council.agents.base import BaseAgent
from council.orchestration.events import Event, EventType


@dataclass
class QAAgent(BaseAgent):
    """
    质量保证智能体

    职责:
    - 订阅 CODE_WRITTEN 事件
    - 接收代码后运行测试
    - 发布 TEST_PASSED 或 TEST_FAILED 事件
    """

    capabilities: List[str] = field(default_factory=lambda: ["run_tests", "lint"])

    def __post_init__(self):
        """初始化时自动订阅代码事件"""
        self.logger = logging.getLogger(f"Agent.{self.name}")
        self.subscribe([EventType.CODE_WRITTEN])
        self.logger.info(f"QAAgent '{self.name}' initialized and subscribed.")

    def handle_event(self, event: Event) -> None:
        """
        处理代码事件

        Args:
            event: 接收到的事件
        """
        if event.type == EventType.CODE_WRITTEN:
            self._handle_code(event)

    def _handle_code(self, event: Event) -> None:
        """
        处理代码编写事件

        Args:
            event: CODE_WRITTEN 事件
        """
        file_name = event.payload.get("file", "unknown.py")
        lines = event.payload.get("lines", 0)

        self.logger.info(f"QAAgent received code: {file_name} ({lines} lines)")

        # 模拟测试运行 (实际实现中可调用 pytest 等)
        test_passed = True  # 模拟测试通过

        # 发布测试结果事件
        result_type = EventType.TEST_PASSED if test_passed else EventType.TEST_FAILED
        result_event = Event(
            type=result_type,
            source=self.name,
            payload={
                "file": file_name,
                "passed": test_passed,
                "coverage": 0.95,  # 模拟覆盖率
            },
        )
        self.publish(result_event)
        self.logger.info(f"QAAgent published {result_type.value} for {file_name}")


__all__ = ["QAAgent"]
