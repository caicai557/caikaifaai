import sys
from unittest.mock import MagicMock
import os
import json

# Mock litellm
sys.modules["litellm"] = MagicMock()
os.environ["OPENAI_API_KEY"] = "dummy"

import pytest
from council.mcp.protocol import MCPProtocolHandler


@pytest.fixture
def handler(tmp_path):
    # We need to ensure TaskManager uses a temp path.
    # MCPProtocolHandler initializes TaskManager(".") hardcoded.
    # We change directory to tmp_path so TaskManager uses it.

    cwd = os.getcwd()
    os.chdir(tmp_path)
    try:
        h = MCPProtocolHandler()
        yield h
    finally:
        os.chdir(cwd)


def test_mcp_add_task(handler):
    request = {
        "jsonrpc": "2.0",
        "method": "tools/call",
        "id": 1,
        "params": {
            "name": "add_task",
            "arguments": {"title": "MCP Task", "description": "Created via MCP"},
        },
    }
    response = handler.handle_request(request)
    assert "result" in response
    # The result content is a string representation of the dict
    assert "MCP Task" in response["result"]["content"]


def test_mcp_list_tasks(handler):
    # Add a task first directly via skill
    handler.task_skill.add_task("Existing", "Desc")

    request = {
        "jsonrpc": "2.0",
        "method": "tools/call",
        "id": 2,
        "params": {"name": "list_tasks", "arguments": {}},
    }
    response = handler.handle_request(request)
    assert "result" in response
    assert "Existing" in response["result"]["content"]
