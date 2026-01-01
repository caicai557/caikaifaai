# Council Hooks Module
"""
钩子机制 - 在代理生命周期的特定节点触发脚本

核心钩子类型:
- SessionStart: 会话启动初始化
- PreToolUse: 工具执行前安全拦截
- PostToolUse: 工具执行后自动化处理
"""

from council.hooks.base import (
    HookType,
    HookAction,
    HookResult,
    HookContext,
    BaseHook,
)
from council.hooks.manager import HookManager
from council.hooks.session_start import SessionStartHook
from council.hooks.pre_tool_use import PreToolUseHook
from council.hooks.post_tool_use import PostToolUseHook

__all__ = [
    # Base
    "HookType",
    "HookAction",
    "HookResult",
    "HookContext",
    "BaseHook",
    # Manager
    "HookManager",
    # Hooks
    "SessionStartHook",
    "PreToolUseHook",
    "PostToolUseHook",
]
