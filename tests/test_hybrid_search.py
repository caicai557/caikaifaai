"""Test Hybrid RAG Search"""

import sys
from unittest.mock import MagicMock
import os
import tempfile
import shutil

# Mock litellm before any council imports
sys.modules["litellm"] = MagicMock()
os.environ["OPENAI_API_KEY"] = "dummy"

import pytest
from council.memory.vector_memory import VectorMemory


@pytest.fixture
def temp_dir():
    """Create temporary directory"""
    d = tempfile.mkdtemp()
    yield d
    shutil.rmtree(d, ignore_errors=True)


@pytest.fixture
def populated_memory(temp_dir):
    """Create VectorMemory with sample documents"""
    memory = VectorMemory(persist_dir=temp_dir, collection_name="test_hybrid")

    # Add sample documents
    memory.add(
        "Python is a programming language known for simplicity", {"topic": "python"}
    )
    memory.add("JavaScript is used for web development", {"topic": "javascript"})
    memory.add("Machine learning with Python and TensorFlow", {"topic": "ml"})
    memory.add(
        "React is a JavaScript framework for building UIs", {"topic": "javascript"}
    )
    memory.add("FastAPI is a Python web framework", {"topic": "python"})

    return memory


class TestHybridSearch:
    """Test hybrid_search functionality"""

    def test_hybrid_search_basic(self, populated_memory):
        """Test basic hybrid search"""
        results = populated_memory.hybrid_search("Python programming", k=3)

        assert len(results) > 0
        # Python-related docs should be highly ranked
        assert any("Python" in r["document"] for r in results)

    def test_hybrid_search_pure_vector(self, populated_memory):
        """Test with alpha=1 (pure vector search)"""
        results = populated_memory.hybrid_search("web development", k=3, alpha=1.0)

        assert len(results) > 0

    def test_hybrid_search_pure_keyword(self, populated_memory):
        """Test with alpha=0 (pure keyword search)"""
        results = populated_memory.hybrid_search("JavaScript framework", k=3, alpha=0.0)

        assert len(results) > 0
        # Should find JavaScript-related docs
        assert any("JavaScript" in r["document"] for r in results)

    def test_hybrid_search_with_where(self, populated_memory):
        """Test hybrid search with metadata filter"""
        results = populated_memory.hybrid_search(
            "programming language", k=5, where={"topic": "python"}
        )

        # All results should have topic=python
        for r in results:
            assert r["metadata"].get("topic") == "python"

    def test_hybrid_search_empty_query(self, populated_memory):
        """Test with empty query"""
        results = populated_memory.hybrid_search("", k=3)

        # Should return some results from vector search
        assert isinstance(results, list)


class TestKeywordSearch:
    """Test _keyword_search method"""

    def test_keyword_search_basic(self, populated_memory):
        """Test basic keyword search"""
        results = populated_memory._keyword_search("Python programming", k=3)

        assert len(results) > 0
        # Check distance is valid
        for r in results:
            assert 0 <= r["distance"] <= 1

    def test_keyword_search_no_match(self, populated_memory):
        """Test keyword search with no matches"""
        results = populated_memory._keyword_search("xyz123 nonexistent", k=3)

        assert len(results) == 0

    def test_keyword_search_with_where(self, populated_memory):
        """Test keyword search with filter"""
        results = populated_memory._keyword_search(
            "framework", k=5, where={"topic": "javascript"}
        )

        for r in results:
            assert r["metadata"].get("topic") == "javascript"


class TestFuseResults:
    """Test _fuse_results RRF fusion"""

    def test_fuse_basic(self, populated_memory):
        """Test basic result fusion"""
        vector_results = [
            {"document": "doc1", "id": "1", "metadata": {}, "distance": 0.1},
            {"document": "doc2", "id": "2", "metadata": {}, "distance": 0.2},
        ]
        keyword_results = [
            {"document": "doc2", "id": "2", "metadata": {}, "distance": 0.1},
            {"document": "doc3", "id": "3", "metadata": {}, "distance": 0.2},
        ]

        fused = populated_memory._fuse_results(vector_results, keyword_results, 0.5, 3)

        assert len(fused) > 0
        # doc2 should be ranked higher (appears in both)
        assert fused[0]["id"] == "2"

    def test_fuse_empty_vector(self, populated_memory):
        """Test fusion with empty vector results"""
        keyword_results = [
            {"document": "doc1", "id": "1", "metadata": {}, "distance": 0.1},
        ]

        fused = populated_memory._fuse_results([], keyword_results, 0.5, 3)

        assert len(fused) == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
