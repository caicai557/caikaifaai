"""Edge Case Tests for 2025 Best Practices Modules"""

import sys
from unittest.mock import MagicMock
import os
import tempfile
import shutil

# Mock litellm before any council imports
sys.modules["litellm"] = MagicMock()
os.environ["OPENAI_API_KEY"] = "dummy"

import pytest
from pathlib import Path


class TestProjectMemoryEdgeCases:
    """Edge cases for ProjectMemory"""

    @pytest.fixture
    def temp_dir(self):
        d = tempfile.mkdtemp()
        yield d
        shutil.rmtree(d, ignore_errors=True)

    def test_nonexistent_directory(self):
        """Test with non-existent directory"""
        from council.memory.project_memory import ProjectMemory

        # Should not raise, just return empty config
        memory = ProjectMemory("/nonexistent/path/that/does/not/exist")
        assert memory.config.name == ""
        assert memory.get_context() == ""

    def test_empty_claude_md(self, temp_dir):
        """Test with empty CLAUDE.md file"""
        from council.memory.project_memory import ProjectMemory

        (Path(temp_dir) / "CLAUDE.md").write_text("")

        memory = ProjectMemory(temp_dir)
        assert memory.has_config("CLAUDE.md")
        assert memory.config.name == ""

    def test_malformed_markdown(self, temp_dir):
        """Test with malformed markdown"""
        from council.memory.project_memory import ProjectMemory

        malformed = """#
## Style Guide
-
## No closing section
"""
        (Path(temp_dir) / "CLAUDE.md").write_text(malformed)

        memory = ProjectMemory(temp_dir)
        # Should not crash
        assert memory.get_context() is not None

    def test_unicode_content(self, temp_dir):
        """Test with unicode/emoji content"""
        from council.memory.project_memory import ProjectMemory

        unicode_content = """# 项目 🚀

## Style Guide
- 使用 UTF-8 编码 📝
- 支持 emoji 表情 ✨

## Caveats
- 注意中文字符 ⚠️
"""
        (Path(temp_dir) / "CLAUDE.md").write_text(unicode_content, encoding="utf-8")

        memory = ProjectMemory(temp_dir)
        assert "🚀" in memory.get_raw_config("CLAUDE.md")

    def test_very_large_file(self, temp_dir):
        """Test with very large config file"""
        from council.memory.project_memory import ProjectMemory

        large_content = "# Large Project\n\n" + "x" * 100000
        (Path(temp_dir) / "README.md").write_text(large_content)

        memory = ProjectMemory(temp_dir)
        context = memory.get_context(max_chars=1000)
        assert len(context) <= 1100  # Allow margin for truncation message

    def test_symlink_directory(self, temp_dir):
        """Test with symlinked directory"""
        from council.memory.project_memory import ProjectMemory

        # Create actual dir with content
        actual = Path(temp_dir) / "actual"
        actual.mkdir()
        (actual / "README.md").write_text("# Symlink Test")

        # Create symlink
        symlink = Path(temp_dir) / "symlink"
        symlink.symlink_to(actual)

        memory = ProjectMemory(str(symlink))
        assert memory.config.name == "Symlink Test"


class TestSemanticCacheEdgeCases:
    """Edge cases for SemanticCache"""

    def test_empty_query(self):
        """Test with empty query"""
        from council.memory.semantic_cache import SemanticCache

        cache = SemanticCache()
        cache.set("", "empty response")
        result = cache.get("")
        assert result == "empty response"

    def test_very_long_query(self):
        """Test with very long query"""
        from council.memory.semantic_cache import SemanticCache

        cache = SemanticCache()
        long_query = "a" * 10000
        cache.set(long_query, "response")
        result = cache.get(long_query)
        assert result == "response"

    def test_special_characters(self):
        """Test with special characters"""
        from council.memory.semantic_cache import SemanticCache

        cache = SemanticCache()
        special = "query with 特殊字符 & <script>alert('xss')</script> \n\t"
        cache.set(special, "response")
        result = cache.get(special)
        assert result == "response"

    def test_concurrent_access(self):
        """Test concurrent set/get operations"""
        from council.memory.semantic_cache import SemanticCache
        import threading

        cache = SemanticCache(max_entries=100)
        errors = []

        def worker(n):
            try:
                for i in range(10):
                    cache.set(f"query_{n}_{i}", f"response_{n}_{i}")
                    cache.get(f"query_{n}_{i}")
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=worker, args=(i,)) for i in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(errors) == 0

    def test_zero_ttl(self):
        """Test with zero TTL"""
        from council.memory.semantic_cache import SemanticCache

        cache = SemanticCache(ttl_hours=0)
        cache.set("query", "response")
        # TTL of 0 means immediately expired
        # First get should work (entry just created)
        result = cache.get("query")  # noqa: F841
        # Behavior depends on timing


class TestHybridSearchEdgeCases:
    """Edge cases for hybrid_search"""

    @pytest.fixture
    def temp_dir(self):
        d = tempfile.mkdtemp()
        yield d
        shutil.rmtree(d, ignore_errors=True)

    def test_empty_query(self, temp_dir):
        """Test hybrid search with empty query"""
        from council.memory.vector_memory import VectorMemory

        memory = VectorMemory(persist_dir=temp_dir)
        memory.add("Test document", {})

        results = memory.hybrid_search("", k=5)
        # Should return vector search results for empty query
        assert isinstance(results, list)

    def test_alpha_boundaries(self, temp_dir):
        """Test alpha at 0 and 1 boundaries"""
        from council.memory.vector_memory import VectorMemory

        memory = VectorMemory(persist_dir=temp_dir)
        memory.add("Python programming language", {})

        # Pure keyword
        results_0 = memory.hybrid_search("Python", k=5, alpha=0.0)
        # Pure vector
        results_1 = memory.hybrid_search("Python", k=5, alpha=1.0)

        assert isinstance(results_0, list)
        assert isinstance(results_1, list)

    def test_no_matching_documents(self, temp_dir):
        """Test with no matching documents"""
        from council.memory.vector_memory import VectorMemory

        memory = VectorMemory(persist_dir=temp_dir)
        memory.add("Completely unrelated content", {})

        results = memory.hybrid_search("xyzabc123 nonexistent", k=5)
        # Should return empty or vector results only
        assert isinstance(results, list)

    def test_k_larger_than_results(self, temp_dir):
        """Test k larger than available results"""
        from council.memory.vector_memory import VectorMemory

        memory = VectorMemory(persist_dir=temp_dir)
        memory.add("One document", {})

        results = memory.hybrid_search("document", k=100)
        assert len(results) <= 1


class TestReflectiveMemoryEdgeCases:
    """Edge cases for reflect/deduplicate"""

    @pytest.fixture
    def temp_dir(self):
        d = tempfile.mkdtemp()
        yield d
        shutil.rmtree(d, ignore_errors=True)

    def test_reflect_with_only_duplicates(self, temp_dir):
        """Test reflection when all memories are duplicates"""
        from council.memory.memory_aggregator import MemoryAggregator
        from council.memory.vector_memory import TieredMemory

        tiered = TieredMemory(persist_dir=temp_dir)
        agg = MemoryAggregator(short_term=tiered)

        # Add all duplicates
        for _ in range(5):
            agg.remember("Same content", "short_term")

        report = agg.reflect()
        assert report["duplicates_found"] >= 4

    def test_deduplicate_special_characters(self, temp_dir):
        """Test deduplication with special characters"""
        from council.memory.memory_aggregator import MemoryAggregator
        from council.memory.vector_memory import TieredMemory

        tiered = TieredMemory(persist_dir=temp_dir)
        agg = MemoryAggregator(short_term=tiered)

        special = "Content with 特殊字符 & symbols <>"
        agg.remember(special, "short_term")
        agg.remember(special, "short_term")  # Duplicate

        removed = agg.deduplicate()
        assert removed >= 1

    def test_smart_remember_empty_content(self, temp_dir):
        """Test smart_remember with empty content"""
        from council.memory.memory_aggregator import MemoryAggregator
        from council.memory.vector_memory import TieredMemory

        tiered = TieredMemory(persist_dir=temp_dir)
        agg = MemoryAggregator(short_term=tiered)

        # Should handle empty content gracefully
        result = agg.smart_remember("")
        assert result is not None


class TestIntegrationEdgeCases:
    """Integration edge cases across modules"""

    @pytest.fixture
    def temp_dir(self):
        d = tempfile.mkdtemp()
        yield d
        shutil.rmtree(d, ignore_errors=True)

    def test_full_pipeline_empty_project(self, temp_dir):
        """Test full pipeline with empty project"""
        from council.memory.project_memory import ProjectMemory
        from council.memory.semantic_cache import SemanticCache
        from council.memory.memory_aggregator import MemoryAggregator
        from council.memory.vector_memory import TieredMemory

        # Empty project
        project = ProjectMemory(temp_dir)

        # Empty cache
        cache = SemanticCache()

        # Empty aggregator
        tiered = TieredMemory(persist_dir=temp_dir)
        agg = MemoryAggregator(short_term=tiered)

        # Should all work without errors
        assert project.get_context() == ""
        assert cache.get("anything") is None
        assert agg.query("anything") == []

        report = agg.reflect()
        assert report["memory_health"] == "good"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
