"""
RAG Retriever - 检索增强生成

提供:
- 文档检索
- Prompt 增强
- 上下文构建
"""

from typing import List, Dict, Any, Optional

from council.memory.vector_memory import VectorMemory


class RAGRetriever:
    """
    RAG 检索器

    用于:
    - 存储知识文档
    - 语义检索相关内容
    - 增强 LLM Prompt
    """

    def __init__(
        self,
        persist_dir: str = ".chromadb",
        collection_name: str = "rag_documents",
    ):
        self.memory = VectorMemory(persist_dir, collection_name)

    def add_documents(
        self,
        documents: List[Dict[str, Any]],
    ) -> None:
        """
        添加文档列表

        Args:
            documents: 文档列表，每个包含 'text' 和可选 metadata
        """
        for doc in documents:
            text = doc.get("text", doc.get("content", ""))
            metadata = {k: v for k, v in doc.items() if k not in ("text", "content")}
            self.memory.add(text, metadata)

    def add_document(
        self,
        text: str,
        metadata: Optional[Dict] = None,
    ) -> str:
        """添加单个文档"""
        return self.memory.add(text, metadata)

    def retrieve(
        self,
        query: str,
        top_k: int = 5,
        where: Optional[Dict] = None,
    ) -> List[Dict]:
        """
        检索相关文档

        Args:
            query: 查询文本
            top_k: 返回数量
            where: 过滤条件

        Returns:
            相关文档列表
        """
        results = self.memory.search(query, k=top_k, where=where)

        # 转换格式
        return [
            {
                "text": r["document"],
                "metadata": r.get("metadata", {}),
                "score": 1 - r.get("distance", 0),  # 转换为相似度
            }
            for r in results
        ]

    def augment_prompt(
        self,
        query: str,
        prompt_template: str = "Context:\n{context}\n\nQuestion: {query}",
        top_k: int = 3,
        context_separator: str = "\n---\n",
    ) -> str:
        """
        增强 Prompt

        Args:
            query: 用户查询
            prompt_template: 模板 (包含 {context} 和 {query})
            top_k: 检索数量
            context_separator: 上下文分隔符

        Returns:
            增强后的 prompt
        """
        # 检索相关文档
        results = self.retrieve(query, top_k=top_k)

        # 构建上下文
        context_parts = [r["text"] for r in results]
        context = context_separator.join(context_parts)

        # 填充模板
        return prompt_template.format(context=context, query=query)

    def count(self) -> int:
        """获取文档数量"""
        return self.memory.count()

    def clear(self) -> None:
        """清空所有文档"""
        self.memory.clear()


__all__ = ["RAGRetriever"]
