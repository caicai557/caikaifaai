"""
Tests for Vector Memory (RAG Pattern)

TDD: 先写测试，后实现
"""

import pytest
import tempfile
import shutil


# =============================================================
# Test Fixtures
# =============================================================


@pytest.fixture
def temp_persist_dir():
    """临时持久化目录"""
    dir_path = tempfile.mkdtemp()
    yield dir_path
    shutil.rmtree(dir_path, ignore_errors=True)


# =============================================================
# Test: VectorMemory
# =============================================================


class TestVectorMemory:
    """VectorMemory 测试"""

    def test_initialization(self, temp_persist_dir):
        """测试初始化"""
        from council.memory.vector_memory import VectorMemory

        memory = VectorMemory(persist_dir=temp_persist_dir)
        assert memory is not None
        assert memory.collection is not None

    def test_add_and_search(self, temp_persist_dir):
        """测试添加和搜索"""
        from council.memory.vector_memory import VectorMemory

        memory = VectorMemory(persist_dir=temp_persist_dir)

        # 添加文档
        memory.add("Python is a programming language", metadata={"type": "fact"})
        memory.add("JavaScript is used for web development", metadata={"type": "fact"})
        memory.add("Claude is an AI assistant", metadata={"type": "fact"})

        # 搜索
        results = memory.search("programming language Python", k=2)

        assert len(results) > 0
        assert "Python" in results[0]["document"]

    def test_search_with_filter(self, temp_persist_dir):
        """测试带过滤的搜索"""
        from council.memory.vector_memory import VectorMemory

        memory = VectorMemory(persist_dir=temp_persist_dir)

        memory.add("Fact 1", metadata={"category": "tech"})
        memory.add("Fact 2", metadata={"category": "science"})
        memory.add("Fact 3", metadata={"category": "tech"})

        results = memory.search(query="fact", k=10, where={"category": "tech"})

        for r in results:
            assert r["metadata"]["category"] == "tech"

    def test_persistence(self, temp_persist_dir):
        """测试持久化"""
        from council.memory.vector_memory import VectorMemory

        # 第一个实例添加数据
        memory1 = VectorMemory(persist_dir=temp_persist_dir)
        memory1.add("Persistent data test", metadata={"id": "test-1"})
        del memory1

        # 第二个实例应该能读取
        memory2 = VectorMemory(persist_dir=temp_persist_dir)
        results = memory2.search("Persistent", k=1)

        assert len(results) > 0
        assert "Persistent" in results[0]["document"]

    def test_clear(self, temp_persist_dir):
        """测试清空"""
        from council.memory.vector_memory import VectorMemory

        memory = VectorMemory(persist_dir=temp_persist_dir)
        memory.add("To be deleted")
        memory.clear()

        results = memory.search("deleted", k=1)
        assert len(results) == 0

    def test_count(self, temp_persist_dir):
        """测试计数"""
        from council.memory.vector_memory import VectorMemory

        memory = VectorMemory(persist_dir=temp_persist_dir)

        assert memory.count() == 0

        memory.add("Doc 1")
        memory.add("Doc 2")
        memory.add("Doc 3")

        assert memory.count() == 3


# =============================================================
# Test: RAGRetriever
# =============================================================


class TestRAGRetriever:
    """RAG 检索器测试"""

    def test_retriever_initialization(self, temp_persist_dir):
        """测试检索器初始化"""
        from council.memory.rag_retriever import RAGRetriever

        retriever = RAGRetriever(persist_dir=temp_persist_dir)
        assert retriever is not None

    def test_add_documents(self, temp_persist_dir):
        """测试添加文档"""
        from council.memory.rag_retriever import RAGRetriever

        retriever = RAGRetriever(persist_dir=temp_persist_dir)

        documents = [
            {"text": "Document one content", "source": "file1.txt"},
            {"text": "Document two content", "source": "file2.txt"},
        ]

        retriever.add_documents(documents)
        assert retriever.count() == 2

    def test_retrieve_context(self, temp_persist_dir):
        """测试检索上下文"""
        from council.memory.rag_retriever import RAGRetriever

        retriever = RAGRetriever(persist_dir=temp_persist_dir)

        retriever.add_documents(
            [
                {"text": "LangGraph is a framework for building agents"},
                {"text": "CrewAI focuses on role-based collaboration"},
                {"text": "OpenTelemetry provides observability"},
            ]
        )

        context = retriever.retrieve("agent framework", top_k=2)

        assert len(context) <= 2
        assert any("LangGraph" in c["text"] or "agent" in c["text"] for c in context)

    def test_augment_prompt(self, temp_persist_dir):
        """测试增强提示词"""
        from council.memory.rag_retriever import RAGRetriever

        retriever = RAGRetriever(persist_dir=temp_persist_dir)

        retriever.add_documents(
            [
                {"text": "The capital of France is Paris"},
            ]
        )

        augmented = retriever.augment_prompt(
            query="What is the capital of France?",
            prompt_template="Context: {context}\n\nQuestion: {query}",
        )

        assert "Paris" in augmented
        assert "France" in augmented


# =============================================================
# Test: Memory Tiers
# =============================================================


class TestMemoryTiers:
    """多层记忆测试"""

    def test_three_tier_memory(self, temp_persist_dir):
        """测试三层记忆架构"""
        from council.memory.vector_memory import TieredMemory

        memory = TieredMemory(persist_dir=temp_persist_dir)

        # Working memory (ephemeral)
        memory.working.add("Current task context")

        # Short-term (session)
        memory.short_term.add("Recent conversation")

        # Long-term (persistent)
        memory.long_term.add("Learned fact")

        # 清除 working 不影响其他
        memory.working.clear()

        assert memory.short_term.count() == 1
        assert memory.long_term.count() == 1
