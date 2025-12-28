"""
Rolling Context Manager - 滚动上下文管理器

实现 2025 Token Efficiency Best Practice: "Ledger-Pruning" Strategy
通过滑动窗口 + 滚动摘要，将上下文长度从 O(N) 降低到 O(1)。

Reference: doc/COUNCIL_2025_TOKEN_EFFICIENCY.md - Pattern B
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Callable
import json


@dataclass
class RoundEntry:
    """对话轮次记录"""
    role: str
    content: str
    token_count: int
    round_number: int = 0


class RollingContext:
    """
    滚动上下文管理器
    
    维护一个固定大小的"最近历史"窗口，
    超出窗口的旧内容被压缩为摘要。
    
    Usage:
        ctx = RollingContext(max_tokens=8000)
        ctx.set_static_context("你是一个架构师...")
        
        ctx.add_turn("Architect", "我认为这个设计...")
        ctx.add_turn("Coder", "从实现角度...")
        
        prompt = ctx.get_context_for_prompt()
    """
    
    def __init__(
        self,
        max_tokens: int = 8000,
        compression_threshold: float = 0.7,
        summarizer: Optional[Callable[[str], str]] = None,
    ):
        """
        初始化滚动上下文管理器
        
        Args:
            max_tokens: 最大 Token 预算 (用于 recent_history)
            compression_threshold: 触发压缩的阈值 (0-1)
            summarizer: 可选的摘要生成函数 (content -> summary)
        """
        self.max_tokens = max_tokens
        self.compression_threshold = compression_threshold
        self._summarizer = summarizer
        
        # State
        self.static_context: str = ""        # 不可变的系统提示 + 任务
        self.past_summary: str = ""          # 压缩后的历史摘要
        self.recent_history: List[RoundEntry] = []  # 最近的详细轮次
        self._round_counter: int = 0
        
    def set_static_context(self, context: str) -> None:
        """设置静态上下文 (系统提示 + 任务描述)"""
        self.static_context = context
        
    def add_turn(self, role: str, content: Any) -> None:
        """
        添加新的对话轮次
        
        Args:
            role: 发言者角色 (如 "Architect", "Coder")
            content: 发言内容 (str 或 dict)
        """
        self._round_counter += 1
        
        # 序列化内容
        if isinstance(content, dict):
            text = json.dumps(content, ensure_ascii=False)
        else:
            text = str(content)
            
        # 估算 Token 数 (简单估算: ~4 字符 = 1 token)
        est_tokens = len(text) // 4
        
        entry = RoundEntry(
            role=role,
            content=text,
            token_count=est_tokens,
            round_number=self._round_counter,
        )
        self.recent_history.append(entry)
        
        # 检查是否需要压缩
        self._prune_if_needed()
        
    def _prune_if_needed(self) -> None:
        """检查并触发压缩"""
        current_load = sum(r.token_count for r in self.recent_history)
        threshold = self.max_tokens * self.compression_threshold
        
        if current_load > threshold:
            self._compress_oldest_turns()
            
    def _compress_oldest_turns(self) -> None:
        """
        压缩最旧的轮次到摘要
        
        策略: 将前 50% 的轮次移入摘要
        """
        if len(self.recent_history) < 2:
            return
            
        cut_idx = len(self.recent_history) // 2
        to_compress = self.recent_history[:cut_idx]
        self.recent_history = self.recent_history[cut_idx:]
        
        # 生成摘要
        if self._summarizer:
            # 使用外部 LLM 摘要器
            content_to_summarize = "\n".join(
                f"{r.role}: {r.content}" for r in to_compress
            )
            new_summary = self._summarizer(content_to_summarize)
        else:
            # 默认: 简单提取关键点
            new_summary = self._default_summarize(to_compress)
            
        # 追加到历史摘要
        if self.past_summary:
            self.past_summary += f"\n\n{new_summary}"
        else:
            self.past_summary = new_summary
            
    def _default_summarize(self, entries: List[RoundEntry]) -> str:
        """默认摘要策略 (无 LLM)"""
        round_range = f"R{entries[0].round_number}-R{entries[-1].round_number}"
        roles = set(e.role for e in entries)
        previews = [e.content[:50] for e in entries[:3]]
        return f"[{round_range}] 参与者: {', '.join(roles)}. 摘要: {'; '.join(previews)}..."
        
    def get_context_for_prompt(self, include_summary: bool = True) -> str:
        """
        生成用于 LLM 调用的上下文字符串
        
        Args:
            include_summary: 是否包含历史摘要
            
        Returns:
            格式化的上下文字符串
        """
        parts = []
        
        # 1. 静态上下文
        if self.static_context:
            parts.append(self.static_context)
            
        # 2. 历史摘要
        if include_summary and self.past_summary:
            parts.append("=== 历史摘要 (PREVIOUSLY) ===")
            parts.append(self.past_summary)
            
        # 3. 最近对话
        if self.recent_history:
            parts.append("=== 当前对话 (CURRENT) ===")
            for entry in self.recent_history:
                parts.append(f"[R{entry.round_number}] {entry.role}: {entry.content}")
                
        return "\n\n".join(parts)
        
    def get_stats(self) -> Dict[str, Any]:
        """获取上下文统计信息"""
        recent_tokens = sum(r.token_count for r in self.recent_history)
        summary_tokens = len(self.past_summary) // 4
        
        return {
            "recent_rounds": len(self.recent_history),
            "recent_tokens": recent_tokens,
            "summary_tokens": summary_tokens,
            "total_tokens": recent_tokens + summary_tokens,
            "max_tokens": self.max_tokens,
            "utilization": recent_tokens / self.max_tokens if self.max_tokens > 0 else 0,
        }
        
    def reset(self) -> None:
        """重置上下文 (保留静态上下文)"""
        self.past_summary = ""
        self.recent_history = []
        self._round_counter = 0


# 导出
__all__ = [
    "RollingContext",
    "RoundEntry",
]
