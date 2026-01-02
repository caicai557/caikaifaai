"""Test Reflective Memory"""

import sys
from unittest.mock import MagicMock
import os
import tempfile
import shutil

# Mock litellm before any council imports
sys.modules["litellm"] = MagicMock()
os.environ["OPENAI_API_KEY"] = "dummy"

import pytest
from council.memory.memory_aggregator import MemoryAggregator
from council.memory.vector_memory import TieredMemory


@pytest.fixture
def temp_dir():
    """Create temporary directory"""
    d = tempfile.mkdtemp()
    yield d
    shutil.rmtree(d, ignore_errors=True)


@pytest.fixture
def aggregator_with_memories(temp_dir):
    """Create aggregator with sample memories"""
    tiered = TieredMemory(persist_dir=temp_dir)
    agg = MemoryAggregator(short_term=tiered)

    # Add sample memories (some duplicates)
    agg.remember("Important architecture decision about microservices", "short_term")
    agg.remember("Python best practices for type hints", "short_term")
    agg.remember(
        "Important architecture decision about microservices", "short_term"
    )  # Duplicate
    agg.remember("Quick note", "short_term")  # Low importance
    agg.remember("Another quick note", "short_term")  # Low importance

    return agg


class TestReflect:
    """Test reflect method"""

    def test_reflect_basic(self, aggregator_with_memories):
        """Test basic reflection"""
        report = aggregator_with_memories.reflect()

        assert "duplicates_found" in report
        assert "low_importance" in report
        assert "suggestions" in report
        assert "memory_health" in report

    def test_reflect_finds_duplicates(self, aggregator_with_memories):
        """Test reflection finds duplicates"""
        report = aggregator_with_memories.reflect()

        assert report["duplicates_found"] >= 1

    def test_reflect_empty_memory(self, temp_dir):
        """Test reflection with empty memory"""
        tiered = TieredMemory(persist_dir=temp_dir)
        agg = MemoryAggregator(short_term=tiered)

        report = agg.reflect()

        assert report["duplicates_found"] == 0
        assert report["memory_health"] == "good"

    def test_reflect_no_short_term(self):
        """Test reflection without short-term memory"""
        agg = MemoryAggregator()

        report = agg.reflect()

        assert report["duplicates_found"] == 0


class TestDeduplicate:
    """Test deduplicate method"""

    def test_deduplicate_removes_duplicates(self, aggregator_with_memories):
        """Test deduplication removes duplicates"""
        # Check initial count
        initial_count = aggregator_with_memories.short_term.short_term.count()

        # Deduplicate
        removed = aggregator_with_memories.deduplicate()

        # Check result
        assert removed >= 1
        assert aggregator_with_memories.short_term.short_term.count() < initial_count

    def test_deduplicate_empty_memory(self, temp_dir):
        """Test deduplication with empty memory"""
        tiered = TieredMemory(persist_dir=temp_dir)
        agg = MemoryAggregator(short_term=tiered)

        removed = agg.deduplicate()

        assert removed == 0

    def test_deduplicate_no_duplicates(self, temp_dir):
        """Test deduplication when no duplicates exist"""
        tiered = TieredMemory(persist_dir=temp_dir)
        agg = MemoryAggregator(short_term=tiered)

        agg.remember("Unique memory 1", "short_term")
        agg.remember("Unique memory 2", "short_term")
        agg.remember("Unique memory 3", "short_term")

        removed = agg.deduplicate()

        assert removed == 0


class TestSmartRememberIntegration:
    """Test smart_remember with reflection"""

    def test_smart_remember_importance_scoring(self, temp_dir):
        """Test that smart_remember correctly scores and stores"""
        tiered = TieredMemory(persist_dir=temp_dir)
        agg = MemoryAggregator(short_term=tiered)

        # Content should be stored
        agg.smart_remember("Critical security decision: use JWT authentication")

        # Should have stored something
        stats = agg.get_stats()
        assert stats["short_term"]["count"] >= 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
