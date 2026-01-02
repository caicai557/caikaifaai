import sys
from unittest.mock import MagicMock

# Mock litellm before any council imports
sys.modules["litellm"] = MagicMock()

import pytest
from council.tools.data_reducer import DataReducer, AnomalyType


@pytest.fixture
def reducer():
    return DataReducer(max_chars=100, filter_pii=True, extract_stats=True)


def test_reduce_simple(reducer):
    stdout = "Hello World"
    result = reducer.reduce(stdout)
    assert "Hello World" in result


def test_reduce_truncation(reducer):
    stdout = "A" * 200
    result = reducer.reduce(stdout)
    assert len(result) <= 150  # allow some buffer for ellipsis
    assert "truncated" in result or "截断" in result


def test_pii_filtering(reducer):
    stdout = "Contact me at alice@example.com or 123-456-7890"
    result = reducer.reduce(stdout)
    assert "alice@example.com" not in result
    assert "[EMAIL]" in result
    assert "123-456-7890" not in result
    assert (
        "[PHONE]" in result or "[SSN]" in result
    )  # Regex might match either depending on exact pattern


def test_extract_anomalies(reducer):
    log = """
    INFO: Starting process
    ERROR: Connection failed
    WARNING: High latency
    INFO: Completed
    """
    anomalies = reducer.extract_anomalies(log)

    assert len(anomalies) >= 2
    types = [a.type for a in anomalies]
    assert AnomalyType.ERROR in types
    assert AnomalyType.WARNING in types


def test_stats_extraction(reducer):
    log = "ERROR found\nWARNING found\nNormal line"
    stats = reducer.extract_statistics(log)

    assert stats["error_count"] == 1
    assert stats["warning_count"] == 1
    assert stats["total_lines"] == 3
