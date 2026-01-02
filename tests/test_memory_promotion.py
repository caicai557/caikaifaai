"""Test Auto Memory Promotion"""

import sys
from unittest.mock import MagicMock
import os
import tempfile
import shutil

# Mock litellm before any council imports
sys.modules["litellm"] = MagicMock()
os.environ["OPENAI_API_KEY"] = "dummy"

import pytest
from council.memory.vector_memory import TieredMemory


@pytest.fixture
def temp_dir():
    """Create temporary directory for memory storage"""
    d = tempfile.mkdtemp()
    yield d
    shutil.rmtree(d, ignore_errors=True)


def test_increment_access(temp_dir):
    """Test increment_access increases access count"""
    tiered = TieredMemory(persist_dir=temp_dir)

    # Add a document
    doc_id = tiered.short_term.add("Test document", {"key": "value"})

    # Increment access
    count1 = tiered.increment_access("short_term", doc_id)
    assert count1 == 1

    count2 = tiered.increment_access("short_term", doc_id)
    assert count2 == 2

    # Verify metadata was updated
    doc = tiered.short_term.get(doc_id)
    assert doc["metadata"]["access_count"] == 2


def test_increment_access_invalid_tier(temp_dir):
    """Test increment_access with invalid tier raises error"""
    tiered = TieredMemory(persist_dir=temp_dir)

    with pytest.raises(ValueError):
        tiered.increment_access("invalid_tier", "doc_id")


def test_auto_promote_threshold(temp_dir):
    """Test auto_promote promotes documents above threshold"""
    tiered = TieredMemory(persist_dir=temp_dir)
    tiered.AUTO_PROMOTE_ACCESS_COUNT = 3  # Set threshold

    # Add document to short_term
    doc_id = tiered.short_term.add(
        "Important knowledge",
        {"access_count": 5},  # Above threshold
    )

    # Run auto promote
    promoted = tiered.auto_promote()

    assert promoted == 1
    assert tiered.short_term.count() == 0
    assert tiered.long_term.count() == 1


def test_auto_promote_below_threshold(temp_dir):
    """Test auto_promote skips documents below threshold"""
    tiered = TieredMemory(persist_dir=temp_dir)
    tiered.AUTO_PROMOTE_ACCESS_COUNT = 5

    # Add document with low access count
    tiered.short_term.add("Low access document", {"access_count": 2})

    promoted = tiered.auto_promote()

    assert promoted == 0
    assert tiered.short_term.count() == 1  # Still in short_term


def test_apply_decay(temp_dir):
    """Test apply_decay reduces access counts"""
    tiered = TieredMemory(persist_dir=temp_dir)
    tiered.DECAY_FACTOR = 0.5  # 50% decay

    # Add document with access count
    doc_id = tiered.short_term.add("Decaying memory", {"access_count": 10})

    # Apply decay
    affected = tiered.apply_decay("short_term")

    assert affected == 1

    # Verify count was reduced
    doc = tiered.short_term.get(doc_id)
    assert doc["metadata"]["access_count"] == 5  # 10 * 0.5


def test_apply_decay_zero_count(temp_dir):
    """Test apply_decay skips documents with zero access count"""
    tiered = TieredMemory(persist_dir=temp_dir)

    # Add document without access count
    tiered.short_term.add("Fresh memory")

    affected = tiered.apply_decay("short_term")

    assert affected == 0


def test_get_stats(temp_dir):
    """Test get_stats returns correct counts"""
    tiered = TieredMemory(persist_dir=temp_dir)

    tiered.working.add("Working 1")
    tiered.working.add("Working 2")
    tiered.short_term.add("Short 1")
    tiered.long_term.add("Long 1")
    tiered.long_term.add("Long 2")
    tiered.long_term.add("Long 3")

    stats = tiered.get_stats()

    assert stats["working"]["count"] == 2
    assert stats["short_term"]["count"] == 1
    assert stats["long_term"]["count"] == 3


def test_promote_adds_metadata(temp_dir):
    """Test promote adds promoted_from metadata"""
    tiered = TieredMemory(persist_dir=temp_dir)

    doc_id = tiered.short_term.add("To be promoted")
    tiered.promote("short_term", "long_term", doc_id)

    doc = tiered.long_term.get(doc_id)
    assert doc["metadata"]["promoted_from"] == "short_term"


def test_full_lifecycle(temp_dir):
    """Test full memory lifecycle: add -> access -> promote -> decay"""
    tiered = TieredMemory(persist_dir=temp_dir)
    tiered.AUTO_PROMOTE_ACCESS_COUNT = 3
    tiered.DECAY_FACTOR = 0.8

    # 1. Add to short_term
    doc_id = tiered.short_term.add("Important fact")

    # 2. Access multiple times
    tiered.increment_access("short_term", doc_id)
    tiered.increment_access("short_term", doc_id)
    tiered.increment_access("short_term", doc_id)  # Now at 3

    # 3. Auto promote (should promote)
    promoted = tiered.auto_promote()
    assert promoted == 1
    assert tiered.long_term.count() == 1

    # 4. Apply decay to long_term
    tiered.increment_access("long_term", doc_id)  # Access count = 4
    tiered.apply_decay("long_term")

    doc = tiered.long_term.get(doc_id)
    assert doc["metadata"]["access_count"] == 3  # 4 * 0.8 = 3.2 -> 3
