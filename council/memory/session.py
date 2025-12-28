"""
LLMSession - 会话持久化管理
维护每个智能体的独立历史，支持断点续传
"""

from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional
from datetime import datetime
import json
from pathlib import Path


@dataclass
class Message:
    """会话消息"""

    role: str  # "system" | "user" | "assistant"
    content: str
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "role": self.role,
            "content": self.content,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Message":
        return cls(
            role=data["role"],
            content=data["content"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            metadata=data.get("metadata", {}),
        )


@dataclass
class SessionState:
    """会话状态"""

    session_id: str
    agent_name: str
    messages: List[Message] = field(default_factory=list)
    context: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "session_id": self.session_id,
            "agent_name": self.agent_name,
            "messages": [m.to_dict() for m in self.messages],
            "context": self.context,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SessionState":
        return cls(
            session_id=data["session_id"],
            agent_name=data["agent_name"],
            messages=[Message.from_dict(m) for m in data.get("messages", [])],
            context=data.get("context", {}),
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]),
        )


class LLMSession:
    """
    LLM会话管理器

    核心功能:
    1. 维护每个智能体的独立历史
    2. 支持会话持久化和恢复
    3. 管理上下文窗口

    使用示例:
        session = LLMSession("architect", storage_dir="./sessions")

        # 添加消息
        session.add_message("user", "设计登录系统")
        session.add_message("assistant", "好的，我来设计...")

        # 保存会话
        session.save()

        # 恢复会话
        session.load()
    """

    def __init__(
        self,
        agent_name: str,
        session_id: Optional[str] = None,
        storage_dir: str = "./.council_sessions",
        max_messages: int = 100,
    ):
        """
        初始化会话

        Args:
            agent_name: 智能体名称
            session_id: 会话ID，默认自动生成
            storage_dir: 存储目录
            max_messages: 最大消息数量
        """
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)

        self.max_messages = max_messages

        if session_id is None:
            session_id = f"{agent_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        self.state = SessionState(
            session_id=session_id,
            agent_name=agent_name,
        )

    @property
    def session_file(self) -> Path:
        """获取会话文件路径"""
        return self.storage_dir / f"{self.state.session_id}.json"

    def add_message(
<<<<<<< HEAD
        self,
        role: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None
=======
        self, role: str, content: str, metadata: Optional[Dict[str, Any]] = None
>>>>>>> e2df45bcf4fae044c2ec81c7ea50a183bdc8bd86
    ) -> None:
        """
        添加消息

        Args:
            role: 角色 (system/user/assistant)
            content: 消息内容
            metadata: 附加元数据
        """
        msg = Message(
            role=role,
            content=content,
            metadata=metadata or {},
        )
        self.state.messages.append(msg)
        self.state.updated_at = datetime.now()

        # 超过最大数量时裁剪
        if len(self.state.messages) > self.max_messages:
            # 保留系统消息和最近的消息
            system_msgs = [m for m in self.state.messages if m.role == "system"]
            other_msgs = [m for m in self.state.messages if m.role != "system"]
            keep_count = self.max_messages - len(system_msgs)
            self.state.messages = system_msgs + other_msgs[-keep_count:]

    def get_messages(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        获取消息列表（LLM格式）

        Args:
            limit: 限制数量

        Returns:
            消息列表
        """
        msgs = self.state.messages[-limit:] if limit else self.state.messages
        return [{"role": m.role, "content": m.content} for m in msgs]

    def set_context(self, key: str, value: Any) -> None:
        """设置上下文"""
        self.state.context[key] = value
        self.state.updated_at = datetime.now()

    def get_context(self, key: str, default: Any = None) -> Any:
        """获取上下文"""
        return self.state.context.get(key, default)

    def save(self) -> bool:
        """
        保存会话到文件

        Returns:
            是否成功
        """
        try:
            with open(self.session_file, "w", encoding="utf-8") as f:
                json.dump(self.state.to_dict(), f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"保存会话失败: {e}")
            return False

    def load(self, session_id: Optional[str] = None) -> bool:
        """
        从文件加载会话

        Args:
            session_id: 可选的会话ID

        Returns:
            是否成功
        """
        if session_id:
            file_path = self.storage_dir / f"{session_id}.json"
        else:
            file_path = self.session_file

        if not file_path.exists():
            return False

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            self.state = SessionState.from_dict(data)
            return True
        except Exception as e:
            print(f"加载会话失败: {e}")
            return False

    def clear(self) -> None:
        """清空会话"""
        self.state.messages = []
        self.state.context = {}
        self.state.updated_at = datetime.now()

    def list_sessions(self) -> List[str]:
        """列出所有会话"""
        return [f.stem for f in self.storage_dir.glob("*.json")]

    def delete(self) -> bool:
        """删除会话文件"""
        if self.session_file.exists():
            self.session_file.unlink()
            return True
        return False


class SessionManager:
    """
    会话管理器 - 管理多个智能体的会话

    使用示例:
        manager = SessionManager()

        # 获取或创建会话
        architect_session = manager.get_session("Architect")
        coder_session = manager.get_session("Coder")

        # 保存所有会话
        manager.save_all()
    """

    def __init__(self, storage_dir: str = "./.council_sessions"):
        self.storage_dir = storage_dir
        self.sessions: Dict[str, LLMSession] = {}

<<<<<<< HEAD
    def get_session(self, agent_name: str, session_id: Optional[str] = None) -> LLMSession:
=======
    def get_session(
        self, agent_name: str, session_id: Optional[str] = None
    ) -> LLMSession:
>>>>>>> e2df45bcf4fae044c2ec81c7ea50a183bdc8bd86
        """获取或创建会话"""
        key = f"{agent_name}:{session_id or 'default'}"
        if key not in self.sessions:
            self.sessions[key] = LLMSession(
                agent_name=agent_name,
                session_id=session_id,
                storage_dir=self.storage_dir,
            )
        return self.sessions[key]

    def save_all(self) -> int:
        """保存所有会话，返回成功数量"""
        return sum(1 for s in self.sessions.values() if s.save())

    def load_all(self, agent_name: Optional[str] = None) -> int:
        """加载所有会话，返回成功数量"""
        storage = Path(self.storage_dir)
        if not storage.exists():
            return 0

        count = 0
        for file in storage.glob("*.json"):
            session_id = file.stem
            if agent_name and not session_id.startswith(agent_name):
                continue

            # 解析 agent_name
            parts = session_id.split("_")
            if parts:
                name = parts[0]
                session = self.get_session(name, session_id)
                if session.load():
                    count += 1
        return count


# 导出
__all__ = [
    "LLMSession",
    "SessionManager",
    "SessionState",
    "Message",
]
