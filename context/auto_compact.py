"""
Auto-Compact Trigger - 自动压缩触发器

监控 Token 使用率，自动触发上下文压缩。

核心功能:
- Token 使用率监控
- 阈值触发压缩
- 与 RollingContext 集成
"""

from dataclasses import dataclass
from typing import Optional, Callable, Any
from council.context.rolling_context import RollingContext


@dataclass
class CompactEvent:
    """压缩事件"""

    triggered_at: str
    before_tokens: int
    after_tokens: int
    tokens_saved: int
    reason: str


class AutoCompactTrigger:
    """
    自动压缩触发器

    监控 Token 使用并自动触发 RollingContext 压缩。

    Usage:
        trigger = AutoCompactTrigger(threshold_percent=70)
        ctx = RollingContext(max_tokens=8000)

        # 添加内容后检查
        ctx.add_turn("User", "...")
        trigger.check_and_compact(ctx)  # 自动压缩如果超过 70%
    """

    def __init__(
        self,
        threshold_percent: float = 70,
        min_rounds_before_compact: int = 4,
        on_compact: Optional[Callable[[CompactEvent], Any]] = None,
    ):
        """
        初始化触发器

        Args:
            threshold_percent: 触发压缩的使用率阈值 (0-100)
            min_rounds_before_compact: 最少轮次数才触发压缩
            on_compact: 压缩回调函数
        """
        self.threshold_percent = threshold_percent
        self.min_rounds = min_rounds_before_compact
        self.on_compact = on_compact
        self._compact_history: list[CompactEvent] = []

    def get_usage_percent(self, ctx: RollingContext) -> float:
        """获取当前使用率"""
        stats = ctx.get_stats()
        return stats["utilization"] * 100

    def should_compact(self, ctx: RollingContext) -> tuple[bool, str]:
        """
        检查是否应该压缩

        Returns:
            (应否压缩, 原因)
        """
        stats = ctx.get_stats()
        usage = stats["utilization"] * 100
        rounds = stats["recent_rounds"]

        if rounds < self.min_rounds:
            return False, f"轮次太少 ({rounds} < {self.min_rounds})"

        if usage >= self.threshold_percent:
            return True, f"使用率 {usage:.1f}% >= {self.threshold_percent}%"

        return False, f"使用率 {usage:.1f}% < {self.threshold_percent}%"

    def check_and_compact(self, ctx: RollingContext) -> Optional[CompactEvent]:
        """
        检查并执行压缩

        Args:
            ctx: RollingContext 实例

        Returns:
            CompactEvent 如果执行了压缩，否则 None
        """
        should, reason = self.should_compact(ctx)

        if not should:
            return None

        # 记录压缩前状态
        before_stats = ctx.get_stats()
        before_tokens = before_stats["recent_tokens"]

        # 执行压缩
        ctx._compress_oldest_turns()

        # 记录压缩后状态
        after_stats = ctx.get_stats()
        after_tokens = after_stats["recent_tokens"]

        from datetime import datetime

        event = CompactEvent(
            triggered_at=datetime.now().isoformat(),
            before_tokens=before_tokens,
            after_tokens=after_tokens,
            tokens_saved=before_tokens - after_tokens,
            reason=reason,
        )

        self._compact_history.append(event)

        if self.on_compact:
            self.on_compact(event)

        return event

    def get_history(self) -> list[CompactEvent]:
        """获取压缩历史"""
        return self._compact_history

    def get_total_tokens_saved(self) -> int:
        """获取总共节省的 Token"""
        return sum(e.tokens_saved for e in self._compact_history)


class AutoCompactWrapper:
    """
    自动压缩包装器

    包装 RollingContext，每次 add_turn 后自动检查压缩。
    """

    def __init__(
        self,
        ctx: RollingContext,
        threshold_percent: float = 70,
    ):
        self.ctx = ctx
        self.trigger = AutoCompactTrigger(threshold_percent=threshold_percent)

    def add_turn(self, role: str, content: Any) -> Optional[CompactEvent]:
        """添加轮次并检查压缩"""
        self.ctx.add_turn(role, content)
        return self.trigger.check_and_compact(self.ctx)

    def get_context_for_prompt(self, **kwargs) -> str:
        """获取上下文"""
        return self.ctx.get_context_for_prompt(**kwargs)

    def get_stats(self) -> dict:
        """获取统计"""
        stats = self.ctx.get_stats()
        stats["total_tokens_saved"] = self.trigger.get_total_tokens_saved()
        stats["compact_count"] = len(self.trigger.get_history())
        return stats


# 导出
__all__ = [
    "AutoCompactTrigger",
    "AutoCompactWrapper",
    "CompactEvent",
]
