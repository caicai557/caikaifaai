"""
Hooks Base Classes - 钩子基础类定义

定义钩子系统的核心抽象和数据结构。
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional


class HookType(Enum):
    """钩子类型枚举"""

    SESSION_START = "session_start"
    PRE_TOOL_USE = "pre_tool_use"
    POST_TOOL_USE = "post_tool_use"


class HookAction(Enum):
    """钩子动作枚举"""

    ALLOW = "allow"  # 允许继续
    BLOCK = "block"  # 阻止执行
    MODIFY = "modify"  # 修改参数后继续
    RETRY = "retry"  # 触发重试 (用于 PostToolUse)


@dataclass
class HookResult:
    """钩子执行结果"""

    action: HookAction
    message: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    modified_data: Optional[Any] = None
    error: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)

    @property
    def is_success(self) -> bool:
        """是否成功（非阻止）"""
        return self.action != HookAction.BLOCK

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "action": self.action.value,
            "message": self.message,
            "metadata": self.metadata,
            "error": self.error,
            "timestamp": self.timestamp.isoformat(),
        }


@dataclass
class HookContext:
    """钩子执行上下文"""

    hook_type: HookType
    session_id: str
    agent_name: str = "unknown"
    tool_name: Optional[str] = None
    tool_args: Optional[Dict[str, Any]] = None
    tool_result: Optional[Any] = None
    working_dir: str = "."
    env_vars: Dict[str, str] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def with_tool(
        self, name: str, args: Optional[Dict[str, Any]] = None
    ) -> "HookContext":
        """创建带工具信息的新上下文"""
        return HookContext(
            hook_type=self.hook_type,
            session_id=self.session_id,
            agent_name=self.agent_name,
            tool_name=name,
            tool_args=args,
            tool_result=self.tool_result,
            working_dir=self.working_dir,
            env_vars=self.env_vars,
            metadata=self.metadata,
        )


class BaseHook(ABC):
    """
    钩子抽象基类

    所有钩子必须继承此类并实现 execute 方法。

    Usage:
        class MyHook(BaseHook):
            async def execute(self, context: HookContext) -> HookResult:
                # 执行钩子逻辑
                return HookResult(action=HookAction.ALLOW)
    """

    def __init__(self, name: str, priority: int = 100):
        """
        初始化钩子

        Args:
            name: 钩子名称
            priority: 优先级 (数字越小越先执行)
        """
        self.name = name
        self.priority = priority
        self.enabled = True

    @property
    @abstractmethod
    def hook_type(self) -> HookType:
        """返回钩子类型"""
        ...

    @abstractmethod
    async def execute(self, context: HookContext) -> HookResult:
        """
        执行钩子逻辑

        Args:
            context: 钩子执行上下文

        Returns:
            HookResult: 执行结果
        """
        ...

    def enable(self) -> None:
        """启用钩子"""
        self.enabled = True

    def disable(self) -> None:
        """禁用钩子"""
        self.enabled = False

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}(name={self.name!r}, priority={self.priority})"
        )


# 导出
__all__ = [
    "HookType",
    "HookAction",
    "HookResult",
    "HookContext",
    "BaseHook",
]
