"""Test Semantic Cache"""

import sys
from unittest.mock import MagicMock
import os
import time

# Mock litellm before any council imports
sys.modules["litellm"] = MagicMock()
os.environ["OPENAI_API_KEY"] = "dummy"

import pytest
from council.memory.semantic_cache import SemanticCache, CacheEntry


class TestCacheEntry:
    """Test CacheEntry dataclass"""

    def test_create_entry(self):
        """Test creating cache entry"""
        entry = CacheEntry(
            query="What is Python?", response="Python is a programming language."
        )

        assert entry.query == "What is Python?"
        assert entry.response == "Python is a programming language."
        assert entry.hits == 0

    def test_query_hash(self):
        """Test query hash generation"""
        entry1 = CacheEntry(query="test", response="r")
        entry2 = CacheEntry(query="test", response="r")
        entry3 = CacheEntry(query="different", response="r")

        assert entry1.query_hash == entry2.query_hash
        assert entry1.query_hash != entry3.query_hash


class TestSemanticCacheBasic:
    """Test SemanticCache basic functionality"""

    def test_init_no_vector(self):
        """Test initialization without vector memory"""
        cache = SemanticCache()

        assert cache.vector_memory is None
        assert cache.similarity_threshold == 0.85

    def test_set_and_get_exact(self):
        """Test exact match caching"""
        cache = SemanticCache()

        cache.set("What is Python?", "Python is a programming language.")
        result = cache.get("What is Python?")

        assert result == "Python is a programming language."

    def test_get_miss(self):
        """Test cache miss"""
        cache = SemanticCache()

        result = cache.get("Unknown query")
        assert result is None

    def test_hit_counter(self):
        """Test hit counter increments"""
        cache = SemanticCache()

        cache.set("test", "response")
        cache.get("test")
        cache.get("test")

        stats = cache.get_stats()
        assert stats["hits"] == 2
        assert stats["misses"] == 0

    def test_miss_counter(self):
        """Test miss counter increments"""
        cache = SemanticCache()

        cache.get("miss1")
        cache.get("miss2")

        stats = cache.get_stats()
        assert stats["hits"] == 0
        assert stats["misses"] == 2

    def test_invalidate(self):
        """Test cache invalidation"""
        cache = SemanticCache()

        cache.set("query", "response")
        assert cache.get("query") == "response"

        cache.invalidate("query")
        assert cache.get("query") is None

    def test_clear(self):
        """Test clear all cache"""
        cache = SemanticCache()

        cache.set("q1", "r1")
        cache.set("q2", "r2")
        cache.set("q3", "r3")

        count = cache.clear()
        assert count == 3

        assert cache.get("q1") is None
        assert cache.get("q2") is None


class TestSemanticCacheWithVector:
    """Test SemanticCache with VectorMemory"""

    @pytest.fixture
    def mock_vector(self):
        """Create mock vector memory"""
        mock = MagicMock()
        mock.search = MagicMock(
            return_value=[
                {
                    "document": "What is Python programming?",
                    "distance": 0.1,  # High similarity (low distance)
                    "metadata": {
                        "cached_response": "Python is a programming language."
                    },
                }
            ]
        )
        mock.add = MagicMock(return_value="cache_id_123")
        return mock

    def test_semantic_search_hit(self, mock_vector):
        """Test semantic search cache hit"""
        cache = SemanticCache(vector_memory=mock_vector, similarity_threshold=0.8)

        # Query similar to cached
        result = cache.get("Tell me about Python")

        assert result == "Python is a programming language."
        mock_vector.search.assert_called_once()

    def test_semantic_search_miss(self, mock_vector):
        """Test semantic search miss when below threshold"""
        mock_vector.search.return_value = [
            {"document": "Unrelated", "distance": 0.5, "metadata": {}}
        ]

        cache = SemanticCache(vector_memory=mock_vector, similarity_threshold=0.8)

        result = cache.get("Completely different query")
        assert result is None

    def test_set_stores_to_vector(self, mock_vector):
        """Test set stores to vector memory"""
        cache = SemanticCache(vector_memory=mock_vector)

        cache.set("query", "response", {"extra": "meta"})

        mock_vector.add.assert_called_once()
        call_args = mock_vector.add.call_args
        assert call_args[0][0] == "query"
        assert "cached_response" in call_args[0][1]


class TestSemanticCacheTTL:
    """Test cache TTL functionality"""

    def test_max_entries_cleanup(self):
        """Test cleanup is triggered and respects max entries"""
        cache = SemanticCache(max_entries=3)

        cache.set("q1", "r1")
        cache.set("q2", "r2")
        cache.set("q3", "r3")
        cache.set("q4", "r4")

        # Cleanup triggered at start of set(), so 4 entries after 4 sets
        # Next set would remove excess
        cache._cleanup_expired()
        assert len(cache._exact_cache) <= 3


class TestSemanticCacheStats:
    """Test cache statistics"""

    def test_get_stats(self):
        """Test statistics collection"""
        cache = SemanticCache()

        cache.set("q1", "r1")
        cache.set("q2", "r2")
        cache.get("q1")  # Hit
        cache.get("q3")  # Miss

        stats = cache.get_stats()

        assert stats["total_entries"] == 2
        assert stats["hits"] == 1
        assert stats["misses"] == 1
        assert stats["hit_rate"] == 0.5
        assert stats["has_vector_cache"] is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
