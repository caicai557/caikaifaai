#!/usr/bin/env python3
"""
TDD Tests for MCP Protocol Handler.

Acceptance Criteria:
- AC4: MCP 服务器支持 `tools/list` 和 `tools/call`
- AC5: `just verify` 全部通过
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestMCPProtocolHandlerImport:
    """Test that MCPProtocolHandler can be imported."""

    def test_protocol_handler_import(self):
        """Test MCPProtocolHandler can be imported."""
        from council.mcp.protocol import MCPProtocolHandler

        assert MCPProtocolHandler is not None

    def test_protocol_handler_instantiation(self):
        """Test MCPProtocolHandler can be instantiated."""
        from council.mcp.protocol import MCPProtocolHandler

        handler = MCPProtocolHandler()
        assert handler is not None


class TestMCPProtocolToolsList:
    """Tests for tools/list endpoint."""

    def test_tools_list_returns_list(self):
        """Test tools/list returns a list of tools."""
        from council.mcp.protocol import MCPProtocolHandler

        handler = MCPProtocolHandler()
        request = {"jsonrpc": "2.0", "method": "tools/list", "id": 1}

        response = handler.handle_request(request)

        assert "result" in response
        assert "tools" in response["result"]
        assert isinstance(response["result"]["tools"], list)

    def test_tools_list_includes_council_query(self):
        """Test tools/list includes council_query tool."""
        from council.mcp.protocol import MCPProtocolHandler

        handler = MCPProtocolHandler()
        request = {"jsonrpc": "2.0", "method": "tools/list", "id": 1}

        response = handler.handle_request(request)
        tools = response["result"]["tools"]
        tool_names = [t["name"] for t in tools]

        assert "council_query" in tool_names

    def test_tools_list_tool_has_required_fields(self):
        """Test each tool has name, description, and inputSchema."""
        from council.mcp.protocol import MCPProtocolHandler

        handler = MCPProtocolHandler()
        request = {"jsonrpc": "2.0", "method": "tools/list", "id": 1}

        response = handler.handle_request(request)
        tools = response["result"]["tools"]

        for tool in tools:
            assert "name" in tool
            assert "description" in tool
            assert "inputSchema" in tool


class TestMCPProtocolToolsCall:
    """Tests for tools/call endpoint."""

    def test_tools_call_council_query(self):
        """Test calling council_query tool."""
        from council.mcp.protocol import MCPProtocolHandler

        handler = MCPProtocolHandler()
        request = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": "council_query",
                "arguments": {"prompt": "test prompt"},
            },
            "id": 2,
        }

        response = handler.handle_request(request)

        assert "result" in response
        assert "content" in response["result"]

    def test_tools_call_unknown_tool_returns_error(self):
        """Test calling unknown tool returns error."""
        from council.mcp.protocol import MCPProtocolHandler

        handler = MCPProtocolHandler()
        request = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": "unknown_tool",
                "arguments": {},
            },
            "id": 3,
        }

        response = handler.handle_request(request)

        assert "error" in response
        assert "unknown" in response["error"]["message"].lower()

    def test_tools_call_missing_arguments_returns_error(self):
        """Test calling tool without required arguments returns error."""
        from council.mcp.protocol import MCPProtocolHandler

        handler = MCPProtocolHandler()
        request = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": "council_query",
                "arguments": {},  # Missing 'prompt'
            },
            "id": 4,
        }

        response = handler.handle_request(request)

        assert "error" in response


class TestMCPProtocolResourcesList:
    """Tests for resources/list endpoint."""

    def test_resources_list_returns_list(self):
        """Test resources/list returns a list of resources."""
        from council.mcp.protocol import MCPProtocolHandler

        handler = MCPProtocolHandler()
        request = {"jsonrpc": "2.0", "method": "resources/list", "id": 5}

        response = handler.handle_request(request)

        assert "result" in response
        assert "resources" in response["result"]
        assert isinstance(response["result"]["resources"], list)

    def test_resources_list_includes_knowledge_graph(self):
        """Test resources/list includes knowledge_graph resource."""
        from council.mcp.protocol import MCPProtocolHandler

        handler = MCPProtocolHandler()
        request = {"jsonrpc": "2.0", "method": "resources/list", "id": 5}

        response = handler.handle_request(request)
        resources = response["result"]["resources"]
        resource_uris = [r["uri"] for r in resources]

        assert any("knowledge_graph" in uri for uri in resource_uris)


class TestMCPProtocolJSONRPC:
    """Tests for JSON-RPC compliance."""

    def test_response_includes_jsonrpc_version(self):
        """Test response includes jsonrpc version."""
        from council.mcp.protocol import MCPProtocolHandler

        handler = MCPProtocolHandler()
        request = {"jsonrpc": "2.0", "method": "tools/list", "id": 1}

        response = handler.handle_request(request)

        assert response["jsonrpc"] == "2.0"

    def test_response_includes_matching_id(self):
        """Test response includes matching request id."""
        from council.mcp.protocol import MCPProtocolHandler

        handler = MCPProtocolHandler()
        request = {"jsonrpc": "2.0", "method": "tools/list", "id": 42}

        response = handler.handle_request(request)

        assert response["id"] == 42

    def test_unknown_method_returns_error(self):
        """Test unknown method returns error response."""
        from council.mcp.protocol import MCPProtocolHandler

        handler = MCPProtocolHandler()
        request = {"jsonrpc": "2.0", "method": "unknown/method", "id": 1}

        response = handler.handle_request(request)

        assert "error" in response
        assert "code" in response["error"]
        assert response["error"]["code"] == -32601  # Method not found

    def test_invalid_request_returns_error(self):
        """Test invalid request returns error."""
        from council.mcp.protocol import MCPProtocolHandler

        handler = MCPProtocolHandler()
        request = {"invalid": "request"}

        response = handler.handle_request(request)

        assert "error" in response
        assert "code" in response["error"]


class TestMCPProtocolToolSimulatePlan:
    """Tests for simulate_plan tool integration."""

    def test_tools_list_includes_simulate_plan(self):
        """Test tools/list includes simulate_plan tool."""
        from council.mcp.protocol import MCPProtocolHandler

        handler = MCPProtocolHandler()
        request = {"jsonrpc": "2.0", "method": "tools/list", "id": 1}

        response = handler.handle_request(request)
        tools = response["result"]["tools"]
        tool_names = [t["name"] for t in tools]

        assert "simulate_plan" in tool_names

    def test_tools_call_simulate_plan(self):
        """Test calling simulate_plan tool."""
        from council.mcp.protocol import MCPProtocolHandler

        handler = MCPProtocolHandler()
        request = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": "simulate_plan",
                "arguments": {"plan": ["Delete utils.py", "Update main.py"]},
            },
            "id": 6,
        }

        response = handler.handle_request(request)

        assert "result" in response
        assert "content" in response["result"]
        # Result should contain warnings (empty list or list of strings)
        content = response["result"]["content"]
        assert isinstance(content, list) or isinstance(content, str)
