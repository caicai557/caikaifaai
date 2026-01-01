"""
Hook Manager - 钩子管理器

负责注册、管理和触发钩子链。
"""

import logging
from collections import defaultdict
from typing import Dict, List, Optional

from council.hooks.base import (
    BaseHook,
    HookType,
    HookAction,
    HookResult,
    HookContext,
)

logger = logging.getLogger(__name__)


class HookManager:
    """
    钩子管理器

    管理所有注册的钩子，按类型和优先级触发钩子链。

    Usage:
        manager = HookManager()
        manager.register(MyPreToolHook())
        manager.register(MyPostToolHook())

        # 触发钩子
        result = await manager.trigger(HookType.PRE_TOOL_USE, context)
    """

    def __init__(self, max_recursion_depth: int = 3):
        """
        初始化钩子管理器

        Args:
            max_recursion_depth: 最大递归深度（防止循环触发）
        """
        self._hooks: Dict[HookType, List[BaseHook]] = defaultdict(list)
        self._recursion_depth = 0
        self._max_recursion_depth = max_recursion_depth

    def register(self, hook: BaseHook) -> None:
        """
        注册钩子

        Args:
            hook: 钩子实例
        """
        hooks_list = self._hooks[hook.hook_type]
        hooks_list.append(hook)
        # 按优先级排序
        hooks_list.sort(key=lambda h: h.priority)
        logger.info(
            f"Registered hook: {hook.name} (type={hook.hook_type.value}, priority={hook.priority})"
        )

    def unregister(self, hook_name: str, hook_type: Optional[HookType] = None) -> bool:
        """
        注销钩子

        Args:
            hook_name: 钩子名称
            hook_type: 可选的钩子类型（不指定则搜索所有类型）

        Returns:
            是否成功注销
        """
        types_to_search = [hook_type] if hook_type else list(HookType)
        removed = False

        for ht in types_to_search:
            original_len = len(self._hooks[ht])
            self._hooks[ht] = [h for h in self._hooks[ht] if h.name != hook_name]
            if len(self._hooks[ht]) < original_len:
                removed = True
                logger.info(f"Unregistered hook: {hook_name}")

        return removed

    def get_hooks(self, hook_type: HookType) -> List[BaseHook]:
        """
        获取指定类型的所有钩子

        Args:
            hook_type: 钩子类型

        Returns:
            钩子列表（按优先级排序）
        """
        return [h for h in self._hooks[hook_type] if h.enabled]

    async def trigger(
        self,
        hook_type: HookType,
        context: HookContext,
        stop_on_block: bool = True,
    ) -> HookResult:
        """
        触发钩子链

        Args:
            hook_type: 钩子类型
            context: 执行上下文
            stop_on_block: 遇到 BLOCK 时是否停止

        Returns:
            最终的钩子结果（如果有 BLOCK 则返回第一个 BLOCK 结果）
        """
        # 检查递归深度
        if self._recursion_depth >= self._max_recursion_depth:
            logger.warning(
                f"Max recursion depth reached ({self._max_recursion_depth}), skipping hooks"
            )
            return HookResult(
                action=HookAction.ALLOW,
                message="Max recursion depth reached",
                metadata={"skipped": True},
            )

        hooks = self.get_hooks(hook_type)
        if not hooks:
            return HookResult(action=HookAction.ALLOW, message="No hooks registered")

        self._recursion_depth += 1
        try:
            results: List[HookResult] = []
            current_context = context

            for hook in hooks:
                try:
                    logger.debug(f"Executing hook: {hook.name}")
                    result = await hook.execute(current_context)
                    results.append(result)

                    # 如果钩子返回 BLOCK，立即停止
                    if result.action == HookAction.BLOCK and stop_on_block:
                        logger.warning(
                            f"Hook {hook.name} blocked execution: {result.message}"
                        )
                        return result

                    # 如果钩子返回 MODIFY，更新上下文
                    if result.action == HookAction.MODIFY and result.modified_data:
                        if isinstance(result.modified_data, dict):
                            current_context = HookContext(
                                **{**current_context.__dict__, **result.modified_data}
                            )

                except Exception as e:
                    logger.error(f"Hook {hook.name} failed: {e}")
                    # 钩子执行失败不阻止后续执行，但记录错误
                    results.append(
                        HookResult(
                            action=HookAction.ALLOW,
                            message=f"Hook failed: {e}",
                            error=str(e),
                        )
                    )

            # 返回最后一个结果，或者综合结果
            if results:
                # 如果有 RETRY，返回 RETRY
                for r in results:
                    if r.action == HookAction.RETRY:
                        return r
                return results[-1]

            return HookResult(action=HookAction.ALLOW, message="All hooks passed")

        finally:
            self._recursion_depth -= 1

    async def trigger_session_start(self, context: HookContext) -> HookResult:
        """触发会话启动钩子"""
        context.hook_type = HookType.SESSION_START
        return await self.trigger(HookType.SESSION_START, context)

    async def trigger_pre_tool(self, context: HookContext) -> HookResult:
        """触发工具执行前钩子"""
        context.hook_type = HookType.PRE_TOOL_USE
        return await self.trigger(HookType.PRE_TOOL_USE, context)

    async def trigger_post_tool(self, context: HookContext) -> HookResult:
        """触发工具执行后钩子"""
        context.hook_type = HookType.POST_TOOL_USE
        return await self.trigger(HookType.POST_TOOL_USE, context, stop_on_block=False)

    def clear(self) -> None:
        """清空所有钩子"""
        self._hooks.clear()
        logger.info("All hooks cleared")

    @property
    def stats(self) -> Dict[str, int]:
        """返回钩子统计信息"""
        return {ht.value: len(hooks) for ht, hooks in self._hooks.items()}


# 全局钩子管理器实例
_default_manager: Optional[HookManager] = None


def get_hook_manager() -> HookManager:
    """获取全局钩子管理器"""
    global _default_manager
    if _default_manager is None:
        _default_manager = HookManager()
    return _default_manager


def set_hook_manager(manager: HookManager) -> None:
    """设置全局钩子管理器"""
    global _default_manager
    _default_manager = manager


# 导出
__all__ = [
    "HookManager",
    "get_hook_manager",
    "set_hook_manager",
]
