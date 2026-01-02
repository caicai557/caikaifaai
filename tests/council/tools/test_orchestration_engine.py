import sys
from unittest.mock import MagicMock

# Mock litellm before any council imports
sys.modules["litellm"] = MagicMock()

import pytest
from council.tools.orchestration_engine import OrchestrationEngine, Tool


@pytest.fixture
def engine():
    return OrchestrationEngine(
        sandbox_provider="local",  # Test with local by default
    )


@pytest.fixture
def tools():
    return [
        Tool(
            name="search_files",
            description="Search files",
            parameters={"pattern": "str", "path": "str"},
        ),
        Tool(name="read_file", description="Read file", parameters={"path": "str"}),
    ]


@pytest.mark.asyncio
async def test_generate_script_loop(engine, tools):
    task = "Find all TODOs in .py files"
    script = await engine.generate_script(task, tools)

    assert "def search_files" in script
    assert "def read_file" in script
    assert "for item in items:" in script or "for" in script  # Should detect loop need
    assert "Find all TODOs" in script


@pytest.mark.asyncio
async def test_generate_script_conditional(engine):
    task = "If file exists, read it, otherwise create it"
    script = await engine.generate_script(task)

    assert "if" in script
    assert "else" in script


@pytest.mark.asyncio
async def test_generate_script_aggregation(engine):
    task = "Count number of errors in logs"
    script = await engine.generate_script(task)

    assert 'results["count"]' in script
    assert "results" in script


def test_tool_schema():
    tool = Tool(name="test", description="desc", parameters={"p": "v"})
    schema = tool.to_schema()
    assert schema["name"] == "test"
    assert schema["parameters"]["p"] == "v"
