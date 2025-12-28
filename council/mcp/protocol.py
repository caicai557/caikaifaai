"""
MCP Protocol Handler - JSON-RPC 2.0 compliant request handling.

Implements the MCP (Model Context Protocol) specification for:
- tools/list: List available tools
- tools/call: Execute a tool
- resources/list: List available resources

Usage:
    from council.mcp.protocol import MCPProtocolHandler

    handler = MCPProtocolHandler()
    response = handler.handle_request({
        "jsonrpc": "2.0",
        "method": "tools/list",
        "id": 1
    })
"""

from typing import Any, Callable, Dict, List, Optional

from council.memory.knowledge_graph import KnowledgeGraph
from scripts.simulate import simulate_plan


# JSON-RPC 2.0 Error Codes
PARSE_ERROR = -32700
INVALID_REQUEST = -32600
METHOD_NOT_FOUND = -32601
INVALID_PARAMS = -32602
INTERNAL_ERROR = -32603


class MCPProtocolHandler:
    """
    MCP Protocol Handler implementing JSON-RPC 2.0.

    Handles standard MCP methods:
    - tools/list: Returns available tools
    - tools/call: Executes a tool with given arguments
    - resources/list: Returns available resources
    """

    def __init__(self, knowledge_graph: Optional[KnowledgeGraph] = None):
        """
        Initialize the MCP Protocol Handler.

        Args:
            knowledge_graph: Optional KnowledgeGraph for simulate_plan tool.
        """
        self.knowledge_graph = knowledge_graph or KnowledgeGraph()
        self._tools: Dict[str, Dict[str, Any]] = self._register_tools()
        self._resources: List[Dict[str, Any]] = self._register_resources()

    def _register_tools(self) -> Dict[str, Dict[str, Any]]:
        """Register available tools."""
        return {
            "council_query": {
                "name": "council_query",
                "description": "Query the AI Council for multi-model consensus",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "prompt": {
                            "type": "string",
                            "description": "The prompt to send to the council",
                        }
                    },
                    "required": ["prompt"],
                },
                "handler": self._handle_council_query,
            },
            "simulate_plan": {
                "name": "simulate_plan",
                "description": "Simulate a plan to detect potential conflicts",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "plan": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "List of plan steps to simulate",
                        }
                    },
                    "required": ["plan"],
                },
                "handler": self._handle_simulate_plan,
            },
        }

    def _register_resources(self) -> List[Dict[str, Any]]:
        """Register available resources."""
        return [
            {
                "uri": "council://knowledge_graph",
                "name": "Knowledge Graph",
                "description": "Project dependency knowledge graph",
                "mimeType": "application/json",
            },
            {
                "uri": "council://governance/policies",
                "name": "Governance Policies",
                "description": "Active governance policies and risk levels",
                "mimeType": "application/json",
            },
        ]

    def handle_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle a JSON-RPC 2.0 request.

        Args:
            request: The JSON-RPC request object.

        Returns:
            The JSON-RPC response object.
        """
        # Validate basic structure
        if not isinstance(request, dict):
            return self._error_response(None, INVALID_REQUEST, "Invalid request")

        request_id = request.get("id")
        method = request.get("method")

        # Validate required fields
        if "method" not in request:
            return self._error_response(
                request_id, INVALID_REQUEST, "Missing 'method' field"
            )

        # Route to appropriate handler
        if method == "tools/list":
            return self._handle_tools_list(request_id)
        elif method == "tools/call":
            return self._handle_tools_call(request_id, request.get("params", {}))
        elif method == "resources/list":
            return self._handle_resources_list(request_id)
        else:
            return self._error_response(
                request_id, METHOD_NOT_FOUND, f"Method not found: {method}"
            )

    def _success_response(
        self, request_id: Any, result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create a success response."""
        return {"jsonrpc": "2.0", "id": request_id, "result": result}

    def _error_response(
        self, request_id: Any, code: int, message: str, data: Any = None
    ) -> Dict[str, Any]:
        """Create an error response."""
        error = {"code": code, "message": message}
        if data is not None:
            error["data"] = data
        return {"jsonrpc": "2.0", "id": request_id, "error": error}

    def _handle_tools_list(self, request_id: Any) -> Dict[str, Any]:
        """Handle tools/list request."""
        tools = [
            {
                "name": tool["name"],
                "description": tool["description"],
                "inputSchema": tool["inputSchema"],
            }
            for tool in self._tools.values()
        ]
        return self._success_response(request_id, {"tools": tools})

    def _handle_tools_call(
        self, request_id: Any, params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle tools/call request."""
        tool_name = params.get("name")
        arguments = params.get("arguments", {})

        # Validate tool exists
        if tool_name not in self._tools:
            return self._error_response(
                request_id,
                INVALID_PARAMS,
                f"Unknown tool: {tool_name}",
            )

        tool = self._tools[tool_name]
        handler: Callable = tool["handler"]

        # Validate required arguments
        schema = tool["inputSchema"]
        required = schema.get("required", [])
        for req_arg in required:
            if req_arg not in arguments:
                return self._error_response(
                    request_id,
                    INVALID_PARAMS,
                    f"Missing required argument: {req_arg}",
                )

        # Execute tool
        try:
            result = handler(arguments)
            return self._success_response(request_id, {"content": result})
        except Exception as e:
            return self._error_response(
                request_id, INTERNAL_ERROR, f"Tool execution failed: {str(e)}"
            )

    def _handle_resources_list(self, request_id: Any) -> Dict[str, Any]:
        """Handle resources/list request."""
        return self._success_response(request_id, {"resources": self._resources})

    def _handle_council_query(self, arguments: Dict[str, Any]) -> str:
        """
        Handle council_query tool execution.

        This is a placeholder that returns a mock response.
        In production, this would call AICouncilServer.query().
        """
        prompt = arguments.get("prompt", "")
        return f"Council query received: {prompt}"

    def _handle_simulate_plan(self, arguments: Dict[str, Any]) -> List[str]:
        """
        Handle simulate_plan tool execution.

        Uses the knowledge graph to detect potential conflicts.
        """
        plan = arguments.get("plan", [])
        warnings = simulate_plan(plan, self.knowledge_graph)
        return warnings


__all__ = ["MCPProtocolHandler"]
