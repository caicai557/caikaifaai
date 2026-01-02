"""Test Context Manager"""

import sys
from unittest.mock import MagicMock
import os

# Mock litellm before any council imports
sys.modules["litellm"] = MagicMock()
os.environ["OPENAI_API_KEY"] = "dummy"

import pytest
from council.context.context_manager import ContextManager, ContextLayer, ContextEntry


def test_context_layer_enum():
    """Test ContextLayer enum values"""
    assert ContextLayer.SYSTEM.value == "system"
    assert ContextLayer.DOCUMENT.value == "document"
    assert ContextLayer.MEMORY.value == "memory"
    assert ContextLayer.SESSION.value == "session"
    assert ContextLayer.TOOL.value == "tool"


def test_context_entry_hash():
    """Test ContextEntry content hash"""
    entry = ContextEntry(layer=ContextLayer.SYSTEM, content="Test content")
    assert len(entry.content_hash) == 16

    # Same content should produce same hash
    entry2 = ContextEntry(layer=ContextLayer.DOCUMENT, content="Test content")
    assert entry.content_hash == entry2.content_hash


def test_add_layer():
    """Test adding context layers"""
    mgr = ContextManager()

    mgr.add_layer(ContextLayer.SYSTEM, "System prompt")
    mgr.add_layer(ContextLayer.DOCUMENT, "Document content", is_cacheable=True)

    stats = mgr.get_stats()
    assert stats["total_entries"] == 2
    assert stats["layer_counts"]["system"] == 1
    assert stats["layer_counts"]["document"] == 1


def test_compile_priority_order():
    """Test compile respects layer priority"""
    mgr = ContextManager()

    # Add in reverse priority order
    mgr.add_layer(ContextLayer.TOOL, "Tool result")
    mgr.add_layer(ContextLayer.SYSTEM, "System prompt")
    mgr.add_layer(ContextLayer.SESSION, "Session data")

    compiled = mgr.compile()

    # System should come first
    assert compiled.index("System prompt") < compiled.index("Session data")
    assert compiled.index("Session data") < compiled.index("Tool result")


def test_compile_max_chars():
    """Test compile truncates at max_chars"""
    mgr = ContextManager(max_context_chars=100)

    mgr.add_layer(ContextLayer.SYSTEM, "A" * 50)
    mgr.add_layer(ContextLayer.DOCUMENT, "B" * 100)

    compiled = mgr.compile()
    assert len(compiled) <= 110  # Allow some margin for truncation marker


def test_clear_layer():
    """Test clear_layer removes specific layer"""
    mgr = ContextManager()

    mgr.add_layer(ContextLayer.SYSTEM, "System")
    mgr.add_layer(ContextLayer.DOCUMENT, "Doc1")
    mgr.add_layer(ContextLayer.DOCUMENT, "Doc2")

    removed = mgr.clear_layer(ContextLayer.DOCUMENT)

    assert removed == 2
    assert mgr.get_stats()["total_entries"] == 1


def test_get_kv_cache_prefix():
    """Test get_kv_cache_prefix only returns cacheable content"""
    mgr = ContextManager()

    mgr.add_layer(ContextLayer.SYSTEM, "System prompt", is_cacheable=True)
    mgr.add_layer(ContextLayer.DOCUMENT, "Large doc", is_cacheable=True)
    mgr.add_layer(ContextLayer.SESSION, "Dynamic session")  # Not cacheable

    prefix = mgr.get_kv_cache_prefix()

    assert "System prompt" in prefix
    assert "Large doc" in prefix
    assert "Dynamic session" not in prefix


def test_get_cache_key():
    """Test get_cache_key produces consistent hashes"""
    mgr1 = ContextManager()
    mgr1.add_layer(ContextLayer.SYSTEM, "Same content", is_cacheable=True)

    mgr2 = ContextManager()
    mgr2.add_layer(ContextLayer.SYSTEM, "Same content", is_cacheable=True)

    assert mgr1.get_cache_key() == mgr2.get_cache_key()


def test_compile_messages():
    """Test compile_messages produces LLM format"""
    mgr = ContextManager()

    mgr.add_layer(ContextLayer.SYSTEM, "You are helpful")
    mgr.add_layer(ContextLayer.DOCUMENT, "Background info")

    messages = mgr.compile_messages()

    assert len(messages) == 2
    assert messages[0]["role"] == "system"
    assert messages[1]["role"] == "user"
    assert "Context" in messages[1]["content"]


def test_get_stats():
    """Test get_stats provides accurate statistics"""
    mgr = ContextManager()

    mgr.add_layer(ContextLayer.SYSTEM, "12345", is_cacheable=True)  # 5 chars
    mgr.add_layer(ContextLayer.DOCUMENT, "6789012345")  # 10 chars

    stats = mgr.get_stats()

    assert stats["total_entries"] == 2
    assert stats["total_chars"] == 15
    assert stats["cacheable_chars"] == 5
