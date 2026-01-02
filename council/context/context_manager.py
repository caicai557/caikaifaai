"""
Context Manager - 上下文分层管理

实现 2025 Context Engineering 最佳实践:
- 分层上下文 (System/Document/Session/Tool)
- 按优先级编译
- KV-Cache 友好的固定前缀提取
"""

from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional
from datetime import datetime
import hashlib


class ContextLayer(Enum):
    """上下文层级 (按优先级排序)"""

    SYSTEM = "system"  # 固定系统提示 (优先级: 0)
    DOCUMENT = "document"  # 缓存的文档 (优先级: 1)
    MEMORY = "memory"  # 长期记忆 (优先级: 2)
    SESSION = "session"  # 会话历史 (优先级: 3)
    TOOL = "tool"  # 工具结果 (优先级: 4)


@dataclass
class ContextEntry:
    """上下文条目"""

    layer: ContextLayer
    content: str
    priority: int = 0  # 同层级内的优先级
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    is_cacheable: bool = False  # 是否可以被 KV-Cache 缓存

    @property
    def content_hash(self) -> str:
        """内容哈希 (用于缓存识别)"""
        return hashlib.sha256(self.content.encode()).hexdigest()[:16]


class ContextManager:
    """
    上下文管理器

    核心功能:
    1. 分层管理不同类型上下文
    2. 按优先级编译最终上下文
    3. 提取可缓存的固定前缀

    Usage:
        ctx_mgr = ContextManager()
        ctx_mgr.add_layer(ContextLayer.SYSTEM, "You are a helpful assistant")
        ctx_mgr.add_layer(ContextLayer.DOCUMENT, large_document, is_cacheable=True)
        ctx_mgr.add_layer(ContextLayer.SESSION, conversation_history)

        # 获取完整上下文
        full_context = ctx_mgr.compile()

        # 获取可缓存前缀
        cache_prefix = ctx_mgr.get_kv_cache_prefix()
    """

    # 层级优先级映射
    LAYER_PRIORITY = {
        ContextLayer.SYSTEM: 0,
        ContextLayer.DOCUMENT: 1,
        ContextLayer.MEMORY: 2,
        ContextLayer.SESSION: 3,
        ContextLayer.TOOL: 4,
    }

    def __init__(self, max_context_chars: int = 100000):
        """
        初始化上下文管理器

        Args:
            max_context_chars: 最大上下文字符数
        """
        self.max_context_chars = max_context_chars
        self._entries: List[ContextEntry] = []

    def add_layer(
        self,
        layer: ContextLayer,
        content: str,
        priority: int = 0,
        is_cacheable: bool = False,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        添加上下文层

        Args:
            layer: 上下文层级
            content: 内容
            priority: 同层级内优先级 (数字越小越优先)
            is_cacheable: 是否可缓存
            metadata: 附加元数据
        """
        entry = ContextEntry(
            layer=layer,
            content=content,
            priority=priority,
            is_cacheable=is_cacheable,
            metadata=metadata or {},
        )
        self._entries.append(entry)

    def clear_layer(self, layer: ContextLayer) -> int:
        """
        清空指定层级的上下文

        Args:
            layer: 要清空的层级

        Returns:
            被清空的条目数
        """
        original_count = len(self._entries)
        self._entries = [e for e in self._entries if e.layer != layer]
        return original_count - len(self._entries)

    def clear_all(self) -> None:
        """清空所有上下文"""
        self._entries.clear()

    def _sort_entries(self) -> List[ContextEntry]:
        """按优先级排序条目"""
        return sorted(
            self._entries, key=lambda e: (self.LAYER_PRIORITY[e.layer], e.priority)
        )

    def compile(self, max_chars: Optional[int] = None) -> str:
        """
        编译完整上下文

        Args:
            max_chars: 最大字符数限制

        Returns:
            编译后的上下文字符串
        """
        limit = max_chars or self.max_context_chars
        sorted_entries = self._sort_entries()

        parts = []
        total_chars = 0

        for entry in sorted_entries:
            if total_chars + len(entry.content) > limit:
                # 截断以适应限制
                remaining = limit - total_chars
                if remaining > 100:  # 至少保留 100 字符
                    parts.append(entry.content[:remaining] + "...(truncated)")
                break

            parts.append(entry.content)
            total_chars += len(entry.content)

        return "\n\n".join(parts)

    def compile_messages(self) -> List[Dict[str, str]]:
        """
        编译为 LLM messages 格式

        Returns:
            消息列表 [{"role": "system", "content": "..."}]
        """
        sorted_entries = self._sort_entries()
        messages = []

        # 合并 SYSTEM 层为一条 system 消息
        system_parts = [
            e.content for e in sorted_entries if e.layer == ContextLayer.SYSTEM
        ]
        if system_parts:
            messages.append({"role": "system", "content": "\n\n".join(system_parts)})

        # 其他层添加为 user 上下文
        other_parts = [
            e.content for e in sorted_entries if e.layer != ContextLayer.SYSTEM
        ]
        if other_parts:
            messages.append(
                {"role": "user", "content": "[Context]\n" + "\n\n".join(other_parts)}
            )

        return messages

    def get_kv_cache_prefix(self) -> str:
        """
        获取可缓存的固定前缀

        只返回标记为 is_cacheable=True 的条目，
        这些内容保持稳定以最大化 KV-Cache 命中率

        Returns:
            可缓存的上下文前缀
        """
        cacheable = [e for e in self._sort_entries() if e.is_cacheable]
        return "\n\n".join(e.content for e in cacheable)

    def get_cache_key(self) -> str:
        """
        获取当前可缓存内容的唯一键

        Returns:
            缓存键 (基于可缓存内容的哈希)
        """
        prefix = self.get_kv_cache_prefix()
        return hashlib.sha256(prefix.encode()).hexdigest()[:32]

    def get_stats(self) -> Dict[str, Any]:
        """
        获取上下文统计

        Returns:
            统计信息字典
        """
        layer_counts = {}
        layer_chars = {}

        for entry in self._entries:
            layer_name = entry.layer.value
            layer_counts[layer_name] = layer_counts.get(layer_name, 0) + 1
            layer_chars[layer_name] = layer_chars.get(layer_name, 0) + len(
                entry.content
            )

        return {
            "total_entries": len(self._entries),
            "total_chars": sum(len(e.content) for e in self._entries),
            "cacheable_chars": len(self.get_kv_cache_prefix()),
            "layer_counts": layer_counts,
            "layer_chars": layer_chars,
        }

    def create_gemini_cache(
        self,
        cache_manager=None,
        cache_name: Optional[str] = None,
        ttl_hours: int = 1,
    ) -> Optional[str]:
        """
        使用 GeminiCacheManager 创建服务端缓存

        将可缓存的上下文前缀发送到 Gemini 服务端缓存，
        实现 ~90% 的 Token 成本节省

        Args:
            cache_manager: GeminiCacheManager 实例
            cache_name: 缓存名称 (默认自动生成)
            ttl_hours: 缓存存活时间 (小时)

        Returns:
            缓存名称，失败时返回 None
        """
        if cache_manager is None:
            try:
                from council.context.gemini_cache import GeminiCacheManager

                cache_manager = GeminiCacheManager()
            except Exception:
                return None

        cache_prefix = self.get_kv_cache_prefix()
        if not cache_prefix:
            return None

        name = cache_name or f"ctx_{self.get_cache_key()[:8]}"

        try:
            return cache_manager.create(
                name=name,
                content=cache_prefix,
                ttl_hours=ttl_hours,
            )
        except Exception:
            return None

    def compile_with_cache_hint(self) -> Dict[str, Any]:
        """
        编译上下文并提供缓存提示

        返回结构化信息供 LLM 调用使用，
        包含可缓存前缀和动态后缀的分离

        Returns:
            {
                "cache_prefix": "...",  # 可缓存的稳定前缀
                "cache_key": "...",     # 缓存键
                "dynamic_suffix": "...", # 动态内容
                "full_context": "...",  # 完整上下文
            }
        """
        cache_prefix = self.get_kv_cache_prefix()

        # 获取非缓存内容
        sorted_entries = self._sort_entries()
        dynamic_parts = [e.content for e in sorted_entries if not e.is_cacheable]
        dynamic_suffix = "\n\n".join(dynamic_parts)

        return {
            "cache_prefix": cache_prefix,
            "cache_key": self.get_cache_key(),
            "dynamic_suffix": dynamic_suffix,
            "full_context": self.compile(),
            "cacheable_ratio": len(cache_prefix)
            / max(1, len(cache_prefix) + len(dynamic_suffix)),
        }


__all__ = [
    "ContextManager",
    "ContextLayer",
    "ContextEntry",
]
