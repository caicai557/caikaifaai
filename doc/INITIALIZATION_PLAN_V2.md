# Initialization Plan V2: 2025 Architecture Upgrade (Detailed)

> **Objective**: Upgrade `caikaifaai` to a "State-of-the-Art" 2025 Multi-Agent System.
> **Architecture**: "Stateful Graph" (Pattern B) + "MCP" (Pattern A) + "Hybrid Memory" (Pattern D).

## Phase 1: Foundation Upgrade (The "Graph" Shift)

> **Goal**: Move from `while` loops to a deterministic State Machine (Graph) for better auditability and cyclic logic.

### 1.1 Implement State Graph Core

**File**: `council/orchestration/graph.py`

```python
from typing import Dict, Any, Callable, List, Optional
from dataclasses import dataclass

@dataclass
class State:
    """The shared state passed between nodes."""
    messages: List[Dict[str, str]]
    context: Dict[str, Any]
    next_node: Optional[str] = None

class Node:
    def __init__(self, name: str, action: Callable[[State], State]):
        self.name = name
        self.action = action

class StateGraph:
    def __init__(self):
        self.nodes: Dict[str, Node] = {}
        self.edges: Dict[str, str] = {} # simple linear edges
        self.conditional_edges: Dict[str, Callable[[State], str]] = {}
        self.entry_point: str = ""

    def add_node(self, name: str, action: Callable):
        self.nodes[name] = Node(name, action)

    def set_entry_point(self, name: str):
        self.entry_point = name

    def add_edge(self, start: str, end: str):
        self.edges[start] = end

    def add_conditional_edge(self, start: str, condition: Callable[[State], str]):
        self.conditional_edges[start] = condition

    def run(self, initial_state: State) -> State:
        current_name = self.entry_point
        state = initial_state

        while current_name:
            print(f"🔄 Executing Node: {current_name}")
            node = self.nodes[current_name]
            state = node.action(state)

            # Determine next node
            if current_name in self.conditional_edges:
                current_name = self.conditional_edges[current_name](state)
            elif current_name in self.edges:
                current_name = self.edges[current_name]
            else:
                current_name = None # End of graph

        return state
```

### 1.2 Integrate Knowledge Graph (Semantic Memory)

**File**: `council/orchestration/semantic_ledger.py`

```python
import networkx as nx
import json

class SemanticLedger:
    """Lightweight Knowledge Graph using NetworkX."""

    def __init__(self):
        self.graph = nx.DiGraph()

    def add_concept(self, name: str, type: str, properties: dict = None):
        self.graph.add_node(name, type=type, **(properties or {}))

    def add_relation(self, source: str, target: str, relation: str):
        self.graph.add_edge(source, target, relation=relation)

    def find_related(self, concept: str, relation: str = None) -> List[str]:
        if concept not in self.graph:
            return []
        if relation:
            return [n for n in self.graph.successors(concept)
                    if self.graph[concept][n].get("relation") == relation]
        return list(self.graph.successors(concept))

    def save(self, path: str):
        data = nx.node_link_data(self.graph)
        with open(path, "w") as f:
            json.dump(data, f)
```

## Phase 2: Protocol Standardization (MCP)

> **Goal**: Adopt the Model Context Protocol (MCP) to standardize how agents access tools and data.

### 2.1 MCP Server Wrapper

**File**: `tools/mcp_server.py`

```python
# Pseudo-code for a simple MCP-compatible server wrapper
# In production, use the official 'mcp' python SDK

class MCPServer:
    def __init__(self, name: str):
        self.name = name
        self.tools = {}

    def register_tool(self, name: str, func: Callable, schema: dict):
        self.tools[name] = {"func": func, "schema": schema}

    def handle_request(self, request: dict) -> dict:
        """Handle JSON-RPC style request from Agent."""
        method = request.get("method")
        if method == "tools/list":
            return {"tools": [{"name": k, "schema": v["schema"]} for k,v in self.tools.items()]}
        elif method == "tools/call":
            tool_name = request.get("params", {}).get("name")
            args = request.get("params", {}).get("arguments", {})
            if tool_name in self.tools:
                result = self.tools[tool_name]["func"](**args)
                return {"content": [{"type": "text", "text": str(result)}]}
        return {"error": "Method not found"}
```

### 2.2 Agent MCP Client

**File**: `council/agents/mcp_client.py`

```python
class MCPClient:
    """Client for Agents to call MCP tools."""

    def __init__(self, server_command: str):
        self.server_command = server_command
        # Initialize stdio connection to server...

    def list_tools(self):
        # Send tools/list request
        pass

    def call_tool(self, name: str, arguments: dict):
        # Send tools/call request
        pass
```

## Phase 3: Predictive Self-Healing (Digital Twin)

> **Goal**: Simulate execution before running it to catch logical errors.

### 3.1 Pre-Flight Simulator

**File**: `scripts/simulate.py`

```python
def simulate_plan(plan: List[str], knowledge_graph: SemanticLedger) -> List[str]:
    """
    Check a plan against the Knowledge Graph for obvious conflicts.
    E.g., "Delete File X" but "File X" is a dependency of "File Y".
    """
    warnings = []
    for step in plan:
        # Simple heuristic check against graph
        if "delete" in step.lower():
            target = extract_target(step)
            dependents = knowledge_graph.find_related(target, relation="dependency_of")
            if dependents:
                warnings.append(f"⚠️ Risk: Deleting {target} breaks {dependents}")
    return warnings
```

---

## Initialization Script (The "Glue")

**File**: `council/init_system.py`

```python
from council.orchestration.graph import StateGraph
from council.orchestration.semantic_ledger import SemanticLedger
from council.agents.planner import PlannerAgent
from council.agents.coder import CoderAgent

def build_council_system():
    # 1. Memory
    kb = SemanticLedger()
    kb.add_concept("UserAuth", "Module")

    # 2. Graph
    workflow = StateGraph()
    workflow.add_node("plan", PlannerAgent(kb).run)
    workflow.add_node("code", CoderAgent().run)

    workflow.set_entry_point("plan")
    workflow.add_edge("plan", "code")

    return workflow

if __name__ == "__main__":
    system = build_council_system()
    final_state = system.run(initial_state=State(messages=[], context={}))
```
