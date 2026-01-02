"""
Vector Memory - ChromaDB 向量记忆

基于 RAG Pattern 实现:
- VectorMemory: 基础向量存储
- TieredMemory: 多层记忆架构
"""

from typing import Dict, List, Any, Optional
from pathlib import Path
import hashlib
import json


def _ensure_httpx_limits() -> None:
    """Patch httpx.Limits for older httpx versions used by chromadb."""
    try:
        import httpx
    except ImportError:
        return

    if hasattr(httpx, "Limits"):
        return

    try:
        from httpx._config import Limits
    except Exception:
        return

    httpx.Limits = Limits


# 尝试导入 ChromaDB
try:
    _ensure_httpx_limits()
    import chromadb

    HAS_CHROMADB = True
except (ImportError, AttributeError):
    HAS_CHROMADB = False
    chromadb = None


class _MockCollection:
    def __init__(self, name: str):
        self.name = name


class VectorMemory:
    """
    向量记忆存储

    使用 ChromaDB 实现语义搜索和持久化
    """

    def __init__(
        self,
        persist_dir: str = ".chromadb",
        collection_name: str = "memory",
    ):
        self.persist_dir = persist_dir
        self.collection_name = collection_name

        if HAS_CHROMADB:
            self.client = chromadb.PersistentClient(path=persist_dir)
            self.collection = self.client.get_or_create_collection(
                name=collection_name,
                metadata={"hnsw:space": "cosine"},
            )
        else:
            # Mock implementation
            self._mock_storage: List[Dict] = []
            self._mock_path = Path(persist_dir) / f"{collection_name}.json"
            self._load_mock_storage()
            self.collection = _MockCollection(collection_name)
            self.client = None

    def _load_mock_storage(self) -> None:
        if not self._mock_path.exists():
            return
        try:
            data = json.loads(self._mock_path.read_text(encoding="utf-8"))
            if isinstance(data, list):
                self._mock_storage = data
        except Exception:
            self._mock_storage = []

    def _persist_mock_storage(self) -> None:
        self._mock_path.parent.mkdir(parents=True, exist_ok=True)
        self._mock_path.write_text(
            json.dumps(self._mock_storage, ensure_ascii=False),
            encoding="utf-8",
        )

    def add(
        self,
        text: str,
        metadata: Optional[Dict[str, Any]] = None,
        doc_id: Optional[str] = None,
    ) -> str:
        """添加文档到向量存储"""
        if doc_id is None:
            doc_id = hashlib.md5(text.encode()).hexdigest()[:12]

        if HAS_CHROMADB:
            self.collection.add(
                documents=[text],
                metadatas=[metadata or {}],
                ids=[doc_id],
            )
        else:
            self._mock_storage.append(
                {
                    "id": doc_id,
                    "document": text,
                    "metadata": metadata or {},
                }
            )
            self._persist_mock_storage()

        return doc_id

    def search(
        self,
        query: str,
        k: int = 5,
        where: Optional[Dict] = None,
    ) -> List[Dict]:
        """语义搜索"""
        if HAS_CHROMADB:
            results = self.collection.query(
                query_texts=[query],
                n_results=k,
                where=where,
            )

            if not results["documents"] or not results["documents"][0]:
                return []

            output = []
            for i, doc in enumerate(results["documents"][0]):
                output.append(
                    {
                        "document": doc,
                        "metadata": results["metadatas"][0][i]
                        if results["metadatas"]
                        else {},
                        "distance": results["distances"][0][i]
                        if results.get("distances")
                        else 0,
                    }
                )
            return output
        else:
            # Mock: 检查 query 中任意单词是否在文档中
            query_words = query.lower().split()
            matches = []
            for item in self._mock_storage:
                # 如果查询为空，返回所有文档
                if not query or not query_words:
                    if where:
                        if all(item["metadata"].get(k) == v for k, v in where.items()):
                            matches.append(item)
                    else:
                        matches.append(item)
                    continue

                doc_lower = item["document"].lower()
                # 检查任意 query 词是否在文档中
                if any(word in doc_lower for word in query_words if len(word) > 2):
                    if where:
                        if all(item["metadata"].get(k) == v for k, v in where.items()):
                            matches.append(item)
                    else:
                        matches.append(item)
            return matches[:k]

    def hybrid_search(
        self,
        query: str,
        k: int = 5,
        alpha: float = 0.5,
        where: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """
        混合搜索: 向量 + 关键词 (BM25 style)

        Args:
            query: 查询文本
            k: 返回结果数
            alpha: 向量搜索权重 (0=纯关键词, 1=纯向量)
            where: 可选的元数据过滤

        Returns:
            融合后的搜索结果
        """
        # 获取向量搜索结果
        vector_results = self.search(query, k=k * 2, where=where)

        # 获取关键词搜索结果 (BM25 style)
        keyword_results = self._keyword_search(query, k=k * 2, where=where)

        # 融合结果
        return self._fuse_results(vector_results, keyword_results, alpha, k)

    def _keyword_search(
        self,
        query: str,
        k: int = 5,
        where: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """BM25 风格的关键词搜索"""
        query_words = query.lower().split()
        if not query_words:
            return []

        results = []

        # 对 mock storage 进行关键词匹配
        for item in self._mock_storage:
            doc = item["document"].lower()

            # 计算词频得分 (简化的 BM25)
            word_count = sum(1 for word in query_words if word in doc and len(word) > 2)
            if word_count == 0:
                continue

            # 检查 where 条件
            if where:
                if not all(item["metadata"].get(k) == v for k, v in where.items()):
                    continue

            # 计算得分 (词频 / 文档长度)
            score = word_count / max(1, len(doc.split()))

            results.append(
                {
                    "document": item["document"],
                    "metadata": item["metadata"],
                    "id": item["id"],
                    "distance": 1 - score,  # 转换为距离
                    "score_type": "keyword",
                }
            )

        # 按得分排序
        results.sort(key=lambda x: x["distance"])
        return results[:k]

    def _fuse_results(
        self,
        vector_results: List[Dict],
        keyword_results: List[Dict],
        alpha: float,
        k: int,
    ) -> List[Dict[str, Any]]:
        """
        Reciprocal Rank Fusion (RRF) 融合结果
        """
        K = 60  # RRF constant
        scores = {}

        # 计算向量搜索的 RRF 分数
        for rank, item in enumerate(vector_results):
            doc_id = item.get("id", item["document"][:50])
            vector_score = alpha / (K + rank + 1)
            scores[doc_id] = scores.get(doc_id, {"item": item, "score": 0})
            scores[doc_id]["score"] += vector_score

        # 计算关键词搜索的 RRF 分数
        for rank, item in enumerate(keyword_results):
            doc_id = item.get("id", item["document"][:50])
            keyword_score = (1 - alpha) / (K + rank + 1)
            if doc_id not in scores:
                scores[doc_id] = {"item": item, "score": 0}
            scores[doc_id]["score"] += keyword_score

        # 按融合分数排序
        sorted_results = sorted(scores.values(), key=lambda x: x["score"], reverse=True)

        return [item["item"] for item in sorted_results[:k]]

    def clear(self) -> None:
        """清空集合"""
        if HAS_CHROMADB:
            self.client.delete_collection(self.collection_name)
            self.collection = self.client.get_or_create_collection(
                name=self.collection_name
            )
        else:
            self._mock_storage.clear()
            if self._mock_path.exists():
                self._mock_path.unlink()

    def get(self, doc_id: str) -> Optional[Dict[str, Any]]:
        """获取单个文档"""
        if HAS_CHROMADB:
            result = self.collection.get(ids=[doc_id])
            if not result["documents"]:
                return None
            return {
                "document": result["documents"][0],
                "metadata": result["metadatas"][0] if result["metadatas"] else {},
                "id": doc_id,
            }
        else:
            for item in self._mock_storage:
                if item["id"] == doc_id:
                    return item
            return None

    def delete(self, doc_id: str) -> None:
        """删除文档"""
        if HAS_CHROMADB:
            self.collection.delete(ids=[doc_id])
        else:
            self._mock_storage = [
                item for item in self._mock_storage if item["id"] != doc_id
            ]
            self._persist_mock_storage()

    def count(self) -> int:
        """获取文档数量"""
        if HAS_CHROMADB:
            return self.collection.count()
        else:
            return len(self._mock_storage)


class TieredMemory:
    """
    多层记忆架构

    - Working: 工作记忆 (短暂)
    - Short-term: 短期记忆 (会话)
    - Long-term: 长期记忆 (持久)

    Features:
    - 自动提升: 基于访问频率自动将记忆从短期提升到长期
    - 衰减机制: 旧记忆逐渐淡化
    """

    # 自动提升阈值
    AUTO_PROMOTE_ACCESS_COUNT = 3
    # 衰减因子 (每次应用衰减时 access_count 减少的比例)
    DECAY_FACTOR = 0.9

    def __init__(self, persist_dir: str = ".chromadb"):
        self.persist_dir = persist_dir
        self.working = VectorMemory(persist_dir, "working_memory")
        self.short_term = VectorMemory(persist_dir, "short_term_memory")
        self.long_term = VectorMemory(persist_dir, "long_term_memory")

    def promote(self, from_tier: str, to_tier: str, doc_id: str) -> None:
        """
        将文档从一层提升到另一层

        Args:
            from_tier: 源层级 (working, short_term, long_term)
            to_tier: 目标层级
            doc_id: 文档 ID
        """
        tiers = {
            "working": self.working,
            "short_term": self.short_term,
            "long_term": self.long_term,
        }

        if from_tier not in tiers or to_tier not in tiers:
            raise ValueError(f"Invalid tier: {from_tier} or {to_tier}")

        source = tiers[from_tier]
        target = tiers[to_tier]

        # 1. 查找源文档
        doc = source.get(doc_id)
        if not doc:
            raise ValueError(f"Document {doc_id} not found in {from_tier}")

        # 2. 添加到目标层
        metadata = doc.get("metadata", {})
        metadata["promoted_from"] = from_tier
        target.add(text=doc["document"], metadata=metadata, doc_id=doc_id)

        # 3. 从源层删除
        source.delete(doc_id)

    def increment_access(self, tier: str, doc_id: str) -> int:
        """
        增加文档访问计数

        Args:
            tier: 层级名称
            doc_id: 文档 ID

        Returns:
            更新后的访问计数
        """
        tiers = {
            "working": self.working,
            "short_term": self.short_term,
            "long_term": self.long_term,
        }

        if tier not in tiers:
            raise ValueError(f"Invalid tier: {tier}")

        memory = tiers[tier]
        doc = memory.get(doc_id)

        if not doc:
            return 0

        # 更新 access_count
        metadata = doc.get("metadata", {})
        access_count = metadata.get("access_count", 0) + 1
        metadata["access_count"] = access_count

        # 重新添加更新后的文档 (ChromaDB upsert)
        memory.delete(doc_id)
        memory.add(text=doc["document"], metadata=metadata, doc_id=doc_id)

        return access_count

    def auto_promote(self) -> int:
        """
        自动提升高访问量的短期记忆到长期记忆

        Returns:
            提升的文档数量
        """
        promoted = 0

        # 获取所有短期记忆
        # 使用空查询获取所有文档 (mock 模式)
        try:
            count = self.short_term.count()
            if count == 0:
                return 0

            # 搜索所有文档
            results = self.short_term.search("", k=count)

            for item in results:
                metadata = item.get("metadata", {})
                access_count = metadata.get("access_count", 0)

                if access_count >= self.AUTO_PROMOTE_ACCESS_COUNT:
                    doc_id = item.get("id")
                    if doc_id:
                        try:
                            self.promote("short_term", "long_term", doc_id)
                            promoted += 1
                        except Exception:
                            pass
        except Exception:
            pass

        return promoted

    def apply_decay(self, tier: str = "short_term") -> int:
        """
        应用衰减机制，降低旧记忆的访问计数

        Args:
            tier: 要应用衰减的层级

        Returns:
            受影响的文档数量
        """
        tiers = {
            "working": self.working,
            "short_term": self.short_term,
            "long_term": self.long_term,
        }

        if tier not in tiers:
            raise ValueError(f"Invalid tier: {tier}")

        memory = tiers[tier]
        affected = 0

        try:
            count = memory.count()
            if count == 0:
                return 0

            results = memory.search("", k=count)

            for item in results:
                doc_id = item.get("id")
                if not doc_id:
                    continue

                metadata = item.get("metadata", {})
                access_count = metadata.get("access_count", 0)

                if access_count > 0:
                    # 应用衰减
                    new_count = int(access_count * self.DECAY_FACTOR)
                    metadata["access_count"] = new_count

                    # 更新文档
                    memory.delete(doc_id)
                    memory.add(text=item["document"], metadata=metadata, doc_id=doc_id)
                    affected += 1
        except Exception:
            pass

        return affected

    def get_stats(self) -> Dict[str, Any]:
        """获取各层统计信息"""
        return {
            "working": {
                "count": self.working.count(),
            },
            "short_term": {
                "count": self.short_term.count(),
            },
            "long_term": {
                "count": self.long_term.count(),
            },
        }


__all__ = ["VectorMemory", "TieredMemory"]
