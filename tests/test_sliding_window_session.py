"""Test sliding window session management"""

import sys
from unittest.mock import MagicMock, AsyncMock
import os
import pytest
import tempfile
import shutil

# Mock litellm before imports
sys.modules["litellm"] = MagicMock()
os.environ["OPENAI_API_KEY"] = "dummy"

from council.memory.session import LLMSession, Message


@pytest.fixture
def temp_dir():
    """Create temporary directory for session storage"""
    d = tempfile.mkdtemp()
    yield d
    shutil.rmtree(d)


def test_window_size_parameter(temp_dir):
    """Test window_size parameter is accepted"""
    session = LLMSession(agent_name="test", storage_dir=temp_dir, window_size=10)
    assert session.window_size == 10


def test_trim_to_window(temp_dir):
    """Test _trim_to_window returns correct number of messages"""
    session = LLMSession(agent_name="test", storage_dir=temp_dir, window_size=5)

    # Add system message
    session.add_message("system", "You are a helpful assistant")

    # Add 10 user/assistant messages
    for i in range(10):
        session.add_message("user", f"Message {i}")

    # Should return system + last 5 messages
    window = session._trim_to_window()
    assert len(window) == 6  # 1 system + 5 window
    assert window[0].role == "system"
    assert "Message 9" in window[-1].content


def test_get_messages_with_window(temp_dir):
    """Test get_messages with use_window=True"""
    session = LLMSession(agent_name="test", storage_dir=temp_dir, window_size=3)

    session.add_message("system", "System prompt")
    for i in range(5):
        session.add_message("user", f"User message {i}")

    # Without window - all messages
    all_msgs = session.get_messages()
    assert len(all_msgs) == 6  # 1 system + 5 user

    # With window - limited
    window_msgs = session.get_messages(use_window=True)
    assert len(window_msgs) == 4  # 1 system + 3 window


@pytest.mark.asyncio
async def test_summarize_trimmed_no_llm(temp_dir):
    """Test summarize_trimmed without LLM client"""
    session = LLMSession(agent_name="test", storage_dir=temp_dir, window_size=2)

    for i in range(5):
        session.add_message("user", f"Message {i}")

    summary = await session.summarize_trimmed()
    assert summary is not None
    assert "3 条消息被归档" in summary


@pytest.mark.asyncio
async def test_summarize_trimmed_with_llm(temp_dir):
    """Test summarize_trimmed with mock LLM client"""
    mock_llm = MagicMock()
    mock_llm.complete = AsyncMock(return_value="这是一段关于任务的简要总结")

    session = LLMSession(
        agent_name="test", storage_dir=temp_dir, window_size=2, llm_client=mock_llm
    )

    for i in range(5):
        session.add_message("user", f"Message {i}")

    summary = await session.summarize_trimmed()
    assert summary is not None
    assert "简要总结" in summary


def test_window_with_summary_in_messages(temp_dir):
    """Test that summary is included in windowed messages"""
    session = LLMSession(agent_name="test", storage_dir=temp_dir, window_size=2)

    for i in range(5):
        session.add_message("user", f"Message {i}")

    # Set summary manually
    session._trimmed_summary = "历史对话关于项目设计"

    msgs = session.get_messages(use_window=True)

    # First message should be the summary
    assert msgs[0]["role"] == "system"
    assert "历史摘要" in msgs[0]["content"]
