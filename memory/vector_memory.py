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
    from chromadb.config import Settings

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
                doc_lower = item["document"].lower()
                # 检查任意 query 词是否在文档中
                if any(word in doc_lower for word in query_words if len(word) > 2):
                    if where:
                        if all(item["metadata"].get(k) == v for k, v in where.items()):
                            matches.append(item)
                    else:
                        matches.append(item)
            return matches[:k]

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
    """

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
        target.add(text=doc["document"], metadata=doc["metadata"], doc_id=doc_id)

        # 3. 从源层删除
        source.delete(doc_id)


__all__ = ["VectorMemory", "TieredMemory"]
