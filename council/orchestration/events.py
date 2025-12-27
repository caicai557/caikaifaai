"""
Event Definitions - 2025 AGI 编排层
定义了系统中的标准事件类型和数据结构。
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict
from datetime import datetime
import uuid


class EventType(Enum):
    """标准事件类型"""

    # 任务生命周期
    TASK_CREATED = "task.created"
    TASK_UPDATED = "task.updated"
    TASK_COMPLETED = "task.completed"
    TASK_FAILED = "task.failed"

    # 信息流
    FACT_DISCOVERED = "info.fact_discovered"  # 发现新事实
    QUERY_RAISED = "info.query_raised"  # 提出新问题
    QUERY_RESOLVED = "info.query_resolved"  # 问题已解决

    # 代码产出
    CODE_WRITTEN = "artifact.code_written"
    TEST_PASSED = "artifact.test_passed"
    TEST_FAILED = "artifact.test_failed"

    # 系统信号
    HEARTBEAT = "system.heartbeat"
    ERROR = "system.error"


@dataclass
class Event:
    """
    标准事件对象

    Attributes:
        type: 事件类型
        source: 事件源 (Agent Name or Component ID)
        payload: 事件携带的数据
        event_id: 唯一ID
        timestamp: 时间戳
    """

    type: EventType
    source: str
    payload: Dict[str, Any] = field(default_factory=dict)
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.event_id,
            "type": self.type.value,
            "source": self.source,
            "payload": self.payload,
            "timestamp": self.timestamp.isoformat(),
        }

    @classmethod
    def create(cls, type_str: str, source: str, **kwargs) -> "Event":
        """
        PTC 友好工厂方法 - 允许通过字符串创建事件

        Usage:
            Event.create("code_written", "coder", file="main.py")
        """
        # 尝试匹配 EventType
        try:
            # 1. 尝试直接匹配 value (e.g. "artifact.code_written")
            event_type = next(e for e in EventType if e.value == type_str)
        except StopIteration:
            try:
                # 2. 尝试匹配 name (e.g. "CODE_WRITTEN")
                event_type = EventType[type_str.upper()]
            except KeyError:
                # 3. 默认归类为 INFO
                event_type = EventType.FACT_DISCOVERED
                kwargs["original_type"] = type_str

        return cls(type=event_type, source=source, payload=kwargs)
