"""
Memory Aggregator - 统一记忆层

整合多种记忆类型提供统一访问接口:
- Short-term (会话记忆)
- Long-term (向量记忆)
- Entity (知识图谱)
"""

from typing import Dict, List, Any, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class MemoryAggregator:
    """
    统一记忆聚合器

    整合 Short-term、Long-term、Entity 记忆,
    提供统一查询和智能记忆路由

    Usage:
        from council.memory.vector_memory import TieredMemory, VectorMemory
        from council.memory.knowledge_graph import KnowledgeGraph

        aggregator = MemoryAggregator(
            short_term=TieredMemory(),
            long_term=VectorMemory(),
            knowledge_graph=KnowledgeGraph()
        )

        # 查询所有记忆源
        results = aggregator.query("项目架构设计")

        # 智能记忆
        aggregator.remember("用户偏好深色主题", memory_type="long_term")
    """

    def __init__(
        self,
        short_term=None,
        long_term=None,
        knowledge_graph=None,
    ):
        """
        初始化记忆聚合器

        Args:
            short_term: TieredMemory 实例
            long_term: VectorMemory 实例
            knowledge_graph: KnowledgeGraph 实例
        """
        self.short_term = short_term
        self.long_term = long_term
        self.knowledge_graph = knowledge_graph

        self._consolidation_threshold = 5  # 短期记忆达到此数量时触发整合

    def query(
        self, query_text: str, sources: Optional[List[str]] = None, k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        多源记忆查询

        Args:
            query_text: 查询文本
            sources: 要查询的源 ["short_term", "long_term", "knowledge_graph"]
                    None 表示查询所有
            k: 每个源返回的最大结果数

        Returns:
            聚合的查询结果列表
        """
        if sources is None:
            sources = ["short_term", "long_term", "knowledge_graph"]

        results = []

        # 查询 Short-term (TieredMemory.working)
        if "short_term" in sources and self.short_term:
            try:
                st_results = self.short_term.working.search(query_text, k=k)
                for r in st_results:
                    results.append(
                        {
                            "source": "short_term",
                            "content": r.get("document", ""),
                            "metadata": r.get("metadata", {}),
                            "distance": r.get("distance", 0),
                        }
                    )
            except Exception as e:
                logger.warning(f"Short-term memory query failed: {e}")

        # 查询 Long-term (VectorMemory)
        if "long_term" in sources and self.long_term:
            try:
                lt_results = self.long_term.search(query_text, k=k)
                for r in lt_results:
                    results.append(
                        {
                            "source": "long_term",
                            "content": r.get("document", ""),
                            "metadata": r.get("metadata", {}),
                            "distance": r.get("distance", 0),
                        }
                    )
            except Exception as e:
                logger.warning(f"Long-term memory query failed: {e}")

        # 查询 Knowledge Graph
        if "knowledge_graph" in sources and self.knowledge_graph:
            try:
                # 使用混合搜索
                kg_results = self.knowledge_graph.search_hybrid(query_text, limit=k)
                for entity in kg_results:
                    results.append(
                        {
                            "source": "knowledge_graph",
                            "content": entity.get("name", "")
                            if isinstance(entity, dict)
                            else str(entity),
                            "metadata": entity.get("properties", {})
                            if isinstance(entity, dict)
                            else {},
                            "distance": 0,
                        }
                    )
            except Exception as e:
                logger.warning(f"Knowledge graph query failed: {e}")

        # 按距离排序 (越小越相关)
        results.sort(key=lambda x: x.get("distance", 0))

        return results[: k * 2]  # 返回最多 2*k 条结果

    def remember(
        self,
        content: str,
        memory_type: str = "short_term",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        智能记忆路由

        Args:
            content: 要记住的内容
            memory_type: 记忆类型 ["short_term", "long_term", "working"]
            metadata: 附加元数据

        Returns:
            记忆 ID
        """
        metadata = metadata or {}
        metadata["remembered_at"] = datetime.now().isoformat()

        if memory_type == "short_term" and self.short_term:
            doc_id = self.short_term.short_term.add(content, metadata)
            logger.info(f"[MemoryAggregator] 已添加到短期记忆: {doc_id}")
            return doc_id

        elif memory_type == "long_term" and self.long_term:
            doc_id = self.long_term.add(content, metadata)
            logger.info(f"[MemoryAggregator] 已添加到长期记忆: {doc_id}")
            return doc_id

        elif memory_type == "working" and self.short_term:
            doc_id = self.short_term.working.add(content, metadata)
            logger.info(f"[MemoryAggregator] 已添加到工作记忆: {doc_id}")
            return doc_id

        else:
            raise ValueError(
                f"Unknown memory type or memory not configured: {memory_type}"
            )

    def smart_remember(
        self,
        content: str,
        context: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        智能记忆 - 自动分类记忆类型

        根据内容特征自动决定存储位置:
        - 短内容/临时信息 -> working
        - 一般信息 -> short_term
        - 重要信息/关键决策 -> long_term

        Args:
            content: 要记住的内容
            context: 可选的上下文信息 (帮助判断重要性)
            metadata: 附加元数据

        Returns:
            记忆 ID
        """
        # 计算重要性得分
        importance = self._calculate_importance(content, context)

        metadata = metadata or {}
        metadata["importance_score"] = importance
        metadata["auto_classified"] = True

        # 根据重要性选择存储位置
        if importance >= 0.7:
            memory_type = "long_term"
        elif importance >= 0.3:
            memory_type = "short_term"
        else:
            memory_type = "working"

        logger.info(
            f"[MemoryAggregator] smart_remember: importance={importance:.2f} -> {memory_type}"
        )
        return self.remember(content, memory_type, metadata)

    def _calculate_importance(
        self, content: str, context: Optional[str] = None
    ) -> float:
        """
        计算内容重要性得分 (0.0 - 1.0)

        启发式规则:
        - 长度较长 -> 更重要
        - 包含关键词 (决策/结论/重要) -> 更重要
        - 包含代码/数据 -> 更重要
        """
        score = 0.3  # 基础分

        # 长度因素
        if len(content) > 500:
            score += 0.2
        elif len(content) > 200:
            score += 0.1

        # 关键词因素
        importance_keywords = [
            "决策",
            "结论",
            "重要",
            "关键",
            "必须",
            "核心",
            "decision",
            "conclusion",
            "important",
            "critical",
            "must",
            "key",
            "架构",
            "设计",
            "安全",
            "漏洞",
            "错误",
        ]
        content_lower = content.lower()
        keyword_hits = sum(1 for kw in importance_keywords if kw in content_lower)
        score += min(0.3, keyword_hits * 0.1)

        # 代码因素
        if "```" in content or "def " in content or "class " in content:
            score += 0.15

        # 数字/数据因素
        import re

        if re.search(r"\d+\.\d+", content):  # 浮点数
            score += 0.05

        return min(1.0, score)

    def consolidate(self) -> int:
        """
        将短期记忆整合到长期记忆

        Returns:
            整合的记忆数量
        """
        if not self.short_term or not self.long_term:
            return 0

        consolidated = 0

        # 从短期记忆获取所有内容
        try:
            # 获取短期记忆数量
            count = self.short_term.short_term.count()

            if count < self._consolidation_threshold:
                logger.info(
                    f"[MemoryAggregator] 短期记忆不足 {self._consolidation_threshold} 条,跳过整合"
                )
                return 0

            # 这里我们使用一个空查询来获取最相关的内容
            # 实际实现中可能需要更精细的策略
            results = self.short_term.short_term.search("", k=count)

            for item in results:
                content = item.get("document", "")
                metadata = item.get("metadata", {})
                metadata["consolidated_from"] = "short_term"
                metadata["consolidated_at"] = datetime.now().isoformat()

                # 添加到长期记忆
                self.long_term.add(content, metadata)
                consolidated += 1

            # 清空短期记忆
            if consolidated > 0:
                self.short_term.short_term.clear()
                logger.info(
                    f"[MemoryAggregator] 已整合 {consolidated} 条记忆到长期存储"
                )

        except Exception as e:
            logger.error(f"Consolidation failed: {e}")

        return consolidated

    def get_context_for_llm(self, query: str, max_chars: int = 4000) -> str:
        """
        获取格式化的记忆上下文供 LLM 使用

        Args:
            query: 查询文本
            max_chars: 最大字符数

        Returns:
            格式化的上下文字符串
        """
        results = self.query(query, k=5)

        if not results:
            return ""

        parts = ["[相关记忆]"]
        total_chars = len(parts[0])

        for r in results:
            content = r["content"]
            source = r["source"]

            entry = f"- [{source}] {content}"

            if total_chars + len(entry) > max_chars:
                break

            parts.append(entry)
            total_chars += len(entry)

        return "\n".join(parts)

    def get_stats(self) -> Dict[str, Any]:
        """获取记忆统计"""
        stats = {
            "short_term": {"available": False, "count": 0},
            "long_term": {"available": False, "count": 0},
            "knowledge_graph": {"available": False, "count": 0},
        }

        if self.short_term:
            stats["short_term"]["available"] = True
            try:
                stats["short_term"]["count"] = self.short_term.short_term.count()
            except Exception:
                pass

        if self.long_term:
            stats["long_term"]["available"] = True
            try:
                stats["long_term"]["count"] = self.long_term.count()
            except Exception:
                pass

        if self.knowledge_graph:
            stats["knowledge_graph"]["available"] = True
            try:
                kg_stats = self.knowledge_graph.get_stats()
                stats["knowledge_graph"]["count"] = kg_stats.get("entity_count", 0)
            except Exception:
                pass

        return stats

    def reflect(self, llm_client=None) -> Dict[str, Any]:
        """
        反思并优化记忆

        基于 2025 最佳实践的反思型记忆:
        1. 识别重复/冗余记忆
        2. 计算记忆关联性
        3. 生成优化建议

        Args:
            llm_client: 可选的 LLM 客户端 (用于高级反思)

        Returns:
            反思报告
        """
        report = {
            "duplicates_found": 0,
            "low_importance": 0,
            "suggestions": [],
            "memory_health": "good",
        }

        if not self.short_term:
            return report

        try:
            # 获取所有短期记忆
            memories = self.short_term.short_term.search("", k=100)

            if not memories:
                return report

            # 1. 检测重复/相似记忆
            seen_content = {}
            duplicates = []

            for mem in memories:
                content = mem.get("document", "")
                content_key = content[:100].lower().strip()

                if content_key in seen_content:
                    duplicates.append(mem)
                    report["duplicates_found"] += 1
                else:
                    seen_content[content_key] = mem

            # 2. 检测低重要性记忆
            for mem in memories:
                content = mem.get("document", "")
                importance = self._calculate_importance(content)
                if importance < 0.3:
                    report["low_importance"] += 1

            # 3. 生成建议
            if report["duplicates_found"] > 0:
                report["suggestions"].append(
                    f"发现 {report['duplicates_found']} 条重复记忆，建议调用 deduplicate()"
                )

            if report["low_importance"] > len(memories) * 0.5:
                report["suggestions"].append(
                    "超过 50% 的记忆重要性较低，建议调整记忆策略"
                )

            # 4. 评估记忆健康度
            total_issues = report["duplicates_found"] + report["low_importance"]
            if total_issues > len(memories) * 0.3:
                report["memory_health"] = "needs_attention"
            elif total_issues > len(memories) * 0.5:
                report["memory_health"] = "poor"

            logger.info(f"[MemoryAggregator] 反思完成: {report}")

        except Exception as e:
            logger.error(f"Reflection failed: {e}")
            report["error"] = str(e)

        return report

    def deduplicate(self) -> int:
        """
        去除重复记忆

        Returns:
            删除的重复记忆数量
        """
        if not self.short_term:
            return 0

        removed = 0

        try:
            memories = self.short_term.short_term.search("", k=100)
            seen_content = {}
            duplicates_to_remove = []

            for mem in memories:
                content = mem.get("document", "")
                content_key = content[:100].lower().strip()

                if content_key in seen_content:
                    duplicates_to_remove.append(mem.get("id"))
                else:
                    seen_content[content_key] = mem.get("id")

            # 删除重复
            for doc_id in duplicates_to_remove:
                if doc_id:
                    self.short_term.short_term.delete(doc_id)
                    removed += 1

            if removed > 0:
                logger.info(f"[MemoryAggregator] 已删除 {removed} 条重复记忆")

        except Exception as e:
            logger.error(f"Deduplication failed: {e}")

        return removed


__all__ = ["MemoryAggregator"]
