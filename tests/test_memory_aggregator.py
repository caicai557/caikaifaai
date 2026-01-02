"""Test Memory Aggregator"""

import sys
from unittest.mock import MagicMock
import os

# Mock litellm before any council imports
sys.modules["litellm"] = MagicMock()
os.environ["OPENAI_API_KEY"] = "dummy"

import pytest
from council.memory.memory_aggregator import MemoryAggregator


class MockVectorMemory:
    """Mock VectorMemory for testing"""

    def __init__(self):
        self._storage = []

    def add(self, text, metadata=None):
        doc_id = f"doc_{len(self._storage)}"
        self._storage.append(
            {"id": doc_id, "document": text, "metadata": metadata or {}}
        )
        return doc_id

    def search(self, query, k=5, where=None):
        return self._storage[:k]

    def count(self):
        return len(self._storage)

    def clear(self):
        self._storage.clear()


class MockTieredMemory:
    """Mock TieredMemory for testing"""

    def __init__(self):
        self.working = MockVectorMemory()
        self.short_term = MockVectorMemory()
        self.long_term = MockVectorMemory()


class MockKnowledgeGraph:
    """Mock KnowledgeGraph for testing"""

    def __init__(self):
        self._entities = []

    def search_hybrid(self, query, limit=5):
        return self._entities[:limit]

    def get_stats(self):
        return {"entity_count": len(self._entities)}


def test_init_empty():
    """Test MemoryAggregator with no memory sources"""
    agg = MemoryAggregator()
    assert agg.short_term is None
    assert agg.long_term is None
    assert agg.knowledge_graph is None


def test_init_with_sources():
    """Test MemoryAggregator with memory sources"""
    agg = MemoryAggregator(
        short_term=MockTieredMemory(),
        long_term=MockVectorMemory(),
        knowledge_graph=MockKnowledgeGraph(),
    )
    assert agg.short_term is not None
    assert agg.long_term is not None
    assert agg.knowledge_graph is not None


def test_remember_short_term():
    """Test remember adds to short-term memory"""
    tiered = MockTieredMemory()
    agg = MemoryAggregator(short_term=tiered)

    doc_id = agg.remember("Test content", memory_type="short_term")

    assert doc_id is not None
    assert tiered.short_term.count() == 1


def test_remember_long_term():
    """Test remember adds to long-term memory"""
    vector = MockVectorMemory()
    agg = MemoryAggregator(long_term=vector)

    doc_id = agg.remember("Test content", memory_type="long_term")

    assert doc_id is not None
    assert vector.count() == 1


def test_query_all_sources():
    """Test query searches all memory sources"""
    tiered = MockTieredMemory()
    tiered.working.add("Working memory content")

    vector = MockVectorMemory()
    vector.add("Long-term content")

    kg = MockKnowledgeGraph()
    kg._entities = [{"name": "Entity1", "properties": {}}]

    agg = MemoryAggregator(short_term=tiered, long_term=vector, knowledge_graph=kg)

    results = agg.query("test query")

    assert len(results) >= 2  # At least from short_term and long_term


def test_query_specific_sources():
    """Test query with specific sources"""
    tiered = MockTieredMemory()
    tiered.working.add("Working content")

    vector = MockVectorMemory()
    vector.add("Long-term content")

    agg = MemoryAggregator(short_term=tiered, long_term=vector)

    # Query only long_term
    results = agg.query("test", sources=["long_term"])

    assert all(r["source"] == "long_term" for r in results)


def test_get_context_for_llm():
    """Test get_context_for_llm formats output"""
    vector = MockVectorMemory()
    vector.add("Important fact about the project")

    agg = MemoryAggregator(long_term=vector)

    context = agg.get_context_for_llm("project info")

    assert "[相关记忆]" in context
    assert "long_term" in context


def test_get_stats():
    """Test get_stats returns correct structure"""
    tiered = MockTieredMemory()
    tiered.short_term.add("item1")
    tiered.short_term.add("item2")

    vector = MockVectorMemory()
    vector.add("long1")

    agg = MemoryAggregator(short_term=tiered, long_term=vector)

    stats = agg.get_stats()

    assert stats["short_term"]["available"] is True
    assert stats["short_term"]["count"] == 2
    assert stats["long_term"]["available"] is True
    assert stats["long_term"]["count"] == 1


def test_consolidate():
    """Test consolidate moves short-term to long-term"""
    tiered = MockTieredMemory()
    vector = MockVectorMemory()

    agg = MemoryAggregator(short_term=tiered, long_term=vector)
    agg._consolidation_threshold = 2  # Lower threshold for test

    # Add enough items to trigger consolidation
    tiered.short_term.add("Memory 1")
    tiered.short_term.add("Memory 2")
    tiered.short_term.add("Memory 3")

    consolidated = agg.consolidate()

    assert consolidated == 3
    assert vector.count() == 3
    assert tiered.short_term.count() == 0


def test_consolidate_below_threshold():
    """Test consolidate skips when below threshold"""
    tiered = MockTieredMemory()
    vector = MockVectorMemory()

    agg = MemoryAggregator(short_term=tiered, long_term=vector)
    agg._consolidation_threshold = 10

    tiered.short_term.add("Memory 1")

    consolidated = agg.consolidate()

    assert consolidated == 0
    assert vector.count() == 0  # Nothing moved
