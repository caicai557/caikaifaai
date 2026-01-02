"""
Semantic Cache - 语义缓存系统

基于语义相似性缓存 LLM 响应，减少重复查询的 API 调用。

Based on 2025 Best Practices: RAG Semantic Caching
"""

from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import hashlib
import logging

logger = logging.getLogger(__name__)


@dataclass
class CacheEntry:
    """缓存条目"""

    query: str
    response: str
    query_embedding: Optional[List[float]] = None
    created_at: datetime = field(default_factory=datetime.now)
    hits: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def query_hash(self) -> str:
        """查询哈希"""
        return hashlib.sha256(self.query.encode()).hexdigest()[:16]


class SemanticCache:
    """
    语义缓存

    基于语义相似性 (而非精确匹配) 缓存 LLM 响应:
    - 相似查询复用已有响应
    - 减少 ~40% LLM 调用
    - 降低延迟和成本

    Usage:
        cache = SemanticCache(vector_memory)

        # 查找缓存
        cached = cache.get("What is Python?")
        if cached:
            return cached

        # 调用 LLM
        response = llm.complete(query)

        # 存储缓存
        cache.set(query, response)
    """

    def __init__(
        self,
        vector_memory=None,
        similarity_threshold: float = 0.85,
        ttl_hours: int = 24,
        max_entries: int = 1000,
    ):
        """
        初始化语义缓存

        Args:
            vector_memory: VectorMemory 实例 (用于语义搜索)
            similarity_threshold: 相似度阈值 (0-1)
            ttl_hours: 缓存存活时间 (小时)
            max_entries: 最大缓存条目数
        """
        self.vector_memory = vector_memory
        self.similarity_threshold = similarity_threshold
        self.ttl = timedelta(hours=ttl_hours)
        self.max_entries = max_entries

        # 内存缓存 (用于快速精确匹配)
        self._exact_cache: Dict[str, CacheEntry] = {}

        # 统计
        self._hits = 0
        self._misses = 0

    def get(self, query: str) -> Optional[str]:
        """
        查找语义缓存

        Args:
            query: 查询文本

        Returns:
            缓存的响应，未命中时返回 None
        """
        # 1. 精确匹配 (最快)
        query_hash = hashlib.sha256(query.encode()).hexdigest()[:16]
        if query_hash in self._exact_cache:
            entry = self._exact_cache[query_hash]
            if self._is_valid(entry):
                entry.hits += 1
                self._hits += 1
                logger.debug(f"[SemanticCache] 精确命中: {query[:50]}...")
                return entry.response
            else:
                del self._exact_cache[query_hash]

        # 2. 语义搜索 (较慢但更灵活)
        if self.vector_memory:
            try:
                results = self.vector_memory.search(query, k=1)
                if results:
                    result = results[0]
                    distance = result.get("distance", 1.0)
                    similarity = 1 - distance

                    if similarity >= self.similarity_threshold:
                        cached_response = result.get("metadata", {}).get(
                            "cached_response"
                        )
                        if cached_response:
                            self._hits += 1
                            logger.debug(
                                f"[SemanticCache] 语义命中 (sim={similarity:.2f}): {query[:50]}..."
                            )
                            return cached_response
            except Exception as e:
                logger.warning(f"[SemanticCache] 语义搜索失败: {e}")

        self._misses += 1
        return None

    def set(
        self,
        query: str,
        response: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        存储缓存

        Args:
            query: 查询文本
            response: LLM 响应
            metadata: 附加元数据

        Returns:
            缓存条目 ID
        """
        # 清理过期缓存
        self._cleanup_expired()

        entry = CacheEntry(
            query=query,
            response=response,
            metadata=metadata or {},
        )

        # 1. 存储到精确匹配缓存
        self._exact_cache[entry.query_hash] = entry

        # 2. 存储到向量缓存 (如果可用)
        cache_id = entry.query_hash
        if self.vector_memory:
            try:
                cache_metadata = {
                    "cached_response": response,
                    "cached_at": datetime.now().isoformat(),
                    "type": "semantic_cache",
                    **(metadata or {}),
                }
                cache_id = self.vector_memory.add(query, cache_metadata)
                logger.debug(f"[SemanticCache] 已缓存: {query[:50]}...")
            except Exception as e:
                logger.warning(f"[SemanticCache] 向量存储失败: {e}")

        return cache_id

    def _is_valid(self, entry: CacheEntry) -> bool:
        """检查缓存条目是否有效"""
        return datetime.now() - entry.created_at < self.ttl

    def _cleanup_expired(self) -> int:
        """清理过期缓存"""
        now = datetime.now()
        expired = [
            key
            for key, entry in self._exact_cache.items()
            if now - entry.created_at >= self.ttl
        ]

        for key in expired:
            del self._exact_cache[key]

        # 如果超过最大条目数，删除最旧的
        if len(self._exact_cache) > self.max_entries:
            sorted_entries = sorted(
                self._exact_cache.items(), key=lambda x: x[1].created_at
            )
            to_remove = len(self._exact_cache) - self.max_entries
            for key, _ in sorted_entries[:to_remove]:
                del self._exact_cache[key]
            expired.extend([key for key, _ in sorted_entries[:to_remove]])

        return len(expired)

    def invalidate(self, query: str) -> bool:
        """
        使特定查询的缓存失效

        Args:
            query: 查询文本

        Returns:
            是否成功删除
        """
        query_hash = hashlib.sha256(query.encode()).hexdigest()[:16]
        if query_hash in self._exact_cache:
            del self._exact_cache[query_hash]
            return True
        return False

    def clear(self) -> int:
        """
        清空所有缓存

        Returns:
            删除的条目数
        """
        count = len(self._exact_cache)
        self._exact_cache.clear()

        # 清空向量缓存
        if self.vector_memory:
            try:
                self.vector_memory.clear()
            except Exception:
                pass

        return count

    def get_stats(self) -> Dict[str, Any]:
        """获取缓存统计"""
        total = self._hits + self._misses
        hit_rate = self._hits / total if total > 0 else 0.0

        return {
            "total_entries": len(self._exact_cache),
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate": hit_rate,
            "has_vector_cache": self.vector_memory is not None,
        }


__all__ = ["SemanticCache", "CacheEntry"]
