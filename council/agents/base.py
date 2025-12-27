"""
BaseAgent - 智能体基类
所有专业化智能体的抽象基类，定义了与 Hub 交互的标准接口。
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List

from council.orchestration.hub import Hub
from council.orchestration.events import Event, EventType


@dataclass
class BaseAgent(ABC):
    """
    智能体抽象基类

    Attributes:
        name: 智能体名称 (如 "coder_agent")
        role: 智能体角色 (如 "code_writer")
        hub: 关联的 Hub 实例
        capabilities: 智能体能力列表 (如 ["write_code", "refactor"])
    """

    name: str
    role: str
    hub: Hub
    capabilities: List[str] = field(default_factory=list)

    @abstractmethod
    def handle_event(self, event: Event) -> None:
        """
        处理接收到的事件 (由子类实现)

        Args:
            event: 接收到的事件对象
        """
        pass

    def subscribe(self, event_types: List[EventType]) -> None:
        """
        订阅多个事件类型

        Args:
            event_types: 要订阅的事件类型列表
        """
        self._subscribed_types = getattr(self, "_subscribed_types", [])
        for event_type in event_types:
            self.hub.subscribe(event_type, self.handle_event)
            self._subscribed_types.append(event_type)

    def unsubscribe(self) -> None:
        """从 Hub 取消所有订阅"""
        for event_type in getattr(self, "_subscribed_types", []):
            self.hub.unsubscribe(event_type, self.handle_event)
        self._subscribed_types = []

    def publish(self, event: Event) -> None:
        """
        向 Hub 发布事件

        Args:
            event: 要发布的事件对象
        """
        self.hub.publish(event)

    def shutdown(self) -> None:
        """优雅关闭智能体"""
        self.unsubscribe()

    def __post_init__(self):
        """初始化后钩子，可被子类覆盖"""
        pass
