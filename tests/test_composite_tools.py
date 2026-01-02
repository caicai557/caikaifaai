"""Test Composite Tools"""

import sys
from unittest.mock import MagicMock, AsyncMock
import os

# Mock litellm before any council imports
sys.modules["litellm"] = MagicMock()
os.environ["OPENAI_API_KEY"] = "dummy"

import pytest
from council.tools.composite_tools import CompositeTools


@pytest.fixture
def mock_web_tools():
    """Create mock web tools"""
    mock = MagicMock()
    mock.search = AsyncMock(
        return_value=[
            {"url": "https://example.com/1", "title": "Result 1"},
            {"url": "https://example.com/2", "title": "Result 2"},
        ]
    )
    mock.browse = AsyncMock(return_value="Page content about the topic...")
    return mock


@pytest.fixture
def mock_code_tools():
    """Create mock code tools"""
    mock = MagicMock()
    mock.security_scan = AsyncMock(
        return_value={"issues": [{"type": "sql_injection", "severity": "high"}]}
    )
    mock.quality_check = AsyncMock(
        return_value={"issues": [{"type": "unused_variable", "severity": "low"}]}
    )
    mock.complexity_analysis = AsyncMock(return_value={"cyclomatic": 5, "cognitive": 8})
    return mock


@pytest.fixture
def mock_llm():
    """Create mock LLM client"""
    mock = MagicMock()
    mock.complete = AsyncMock(
        return_value="This is a summary of the research findings."
    )
    return mock


def test_init_empty():
    """Test CompositeTools with no dependencies"""
    tools = CompositeTools()
    assert tools.web_tools is None
    assert tools.code_tools is None


def test_get_tool_definitions():
    """Test get_tool_definitions returns valid structure"""
    tools = CompositeTools()
    defs = tools.get_tool_definitions()

    assert len(defs) == 2
    assert defs[0]["name"] == "deep_research"
    assert defs[1]["name"] == "code_analyze"
    assert "parameters" in defs[0]


@pytest.mark.asyncio
async def test_deep_research(mock_web_tools, mock_llm):
    """Test deep_research with mock tools"""
    tools = CompositeTools(web_tools=mock_web_tools, llm_client=mock_llm)

    result = await tools.deep_research("AI agent best practices")

    assert result["topic"] == "AI agent best practices"
    assert len(result["sources"]) > 0
    assert result["summary"] != ""

    # Verify search was called
    mock_web_tools.search.assert_called_once()


@pytest.mark.asyncio
async def test_deep_research_no_tools():
    """Test deep_research without web tools"""
    tools = CompositeTools()

    result = await tools.deep_research("test topic")

    assert result["topic"] == "test topic"
    assert result["sources"] == []
    assert result["summary"] == ""


@pytest.mark.asyncio
async def test_code_analyze(mock_code_tools):
    """Test code_analyze with mock tools"""
    tools = CompositeTools(code_tools=mock_code_tools)

    result = await tools.code_analyze("/path/to/file.py")

    assert result["file"] == "/path/to/file.py"
    assert len(result["security_issues"]) == 1
    assert len(result["quality_issues"]) == 1
    assert "cyclomatic" in result["complexity"]


@pytest.mark.asyncio
async def test_code_analyze_no_tools():
    """Test code_analyze without code tools"""
    tools = CompositeTools()

    result = await tools.code_analyze("/path/to/file.py")

    assert "No code analysis tools available" in result["summary"]


@pytest.mark.asyncio
async def test_code_analyze_partial(mock_code_tools):
    """Test code_analyze with only security scan"""
    tools = CompositeTools(code_tools=mock_code_tools)

    result = await tools.code_analyze(
        "/path/to/file.py", include_security=True, include_quality=False
    )

    assert len(result["security_issues"]) == 1
    # Quality check should not be called
    mock_code_tools.quality_check.assert_not_called()
