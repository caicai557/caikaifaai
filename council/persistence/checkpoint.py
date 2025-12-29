"""
Checkpoint - 检查点数据结构

基于 LangGraph checkpointing 模式设计
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Any
import json


@dataclass
class Checkpoint:
    """
    状态检查点

    保存 Agent 执行的完整状态快照，支持:
    - 故障恢复
    - 时间旅行调试
    - 多线程隔离

    Attributes:
        thread_id: 线程标识符 (隔离不同会话)
        state: 状态字典 (包含所有需要持久化的数据)
        step: 执行步骤编号
        timestamp: 创建时间
    """

    thread_id: str
    state: Dict[str, Any]
    step: int = 0
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        """序列化为字典"""
        return {
            "thread_id": self.thread_id,
            "state": self.state,
            "step": self.step,
            "timestamp": self.timestamp.isoformat(),
        }

    def to_json(self) -> str:
        """序列化为 JSON"""
        return json.dumps(self.to_dict(), ensure_ascii=False)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Checkpoint":
        """从字典反序列化"""
        try:
            return cls(
                thread_id=data["thread_id"],
                state=data["state"],
                step=data.get("step", 0),
                timestamp=datetime.fromisoformat(data["timestamp"]),
            )
        except KeyError as e:
            raise ValueError(f"Invalid checkpoint data - missing key: {e}")
        except (TypeError, ValueError) as e:
            raise ValueError(f"Invalid checkpoint format: {e}")

    @classmethod
    def from_json(cls, json_str: str) -> "Checkpoint":
        """从 JSON 反序列化"""
        return cls.from_dict(json.loads(json_str))


__all__ = ["Checkpoint"]
