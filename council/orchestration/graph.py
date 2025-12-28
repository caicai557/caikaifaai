"""
StateGraph - State Machine Execution Engine for 2025 Architecture.

Implements Pattern B (Stateful Graph) from 2025 AGI Best Practices.
Provides deterministic state transitions with conditional branching.

Usage:
    graph = StateGraph()
    graph.add_node("plan", planner_action)
    graph.add_node("code", coder_action)
    graph.add_edge("plan", "code")
    graph.set_entry_point("plan")
    final_state = graph.run(initial_state)
"""

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional


@dataclass
class State:
    """Shared state passed between graph nodes.

    Attributes:
        messages: List of message dictionaries (role/content pairs).
        context: Arbitrary context data for the workflow.
        next_node: Optional hint for next node (used by conditional edges).
    """

    messages: List[Dict[str, str]] = field(default_factory=list)
    context: Dict[str, Any] = field(default_factory=dict)
    next_node: Optional[str] = None


# Type alias for node action functions
NodeAction = Callable[[State], State]
# Type alias for conditional edge decision functions
ConditionalDecision = Callable[[State], str]


class StateGraph:
    """State machine graph for workflow execution.

    Supports:
    - Linear node chains via add_edge()
    - Conditional branching via add_conditional_edge()
    - Deterministic execution via run()

    Example:
        >>> graph = StateGraph()
        >>> graph.add_node("start", lambda s: s)
        >>> graph.set_entry_point("start")
        >>> result = graph.run(State())
    """

    def __init__(self) -> None:
        """Initialize an empty state graph."""
        self.nodes: Dict[str, NodeAction] = {}
        self.edges: Dict[str, str] = {}
        self.conditional_edges: Dict[str, ConditionalDecision] = {}
        self.entry_point: str = ""

    def add_node(self, name: str, action: NodeAction) -> None:
        """Add a node with an action function.

        Args:
            name: Unique node identifier.
            action: Function that takes State and returns State.
        """
        self.nodes[name] = action

    def set_entry_point(self, name: str) -> None:
        """Set the starting node for graph execution.

        Args:
            name: Node name to start execution from.
        """
        self.entry_point = name

    def add_edge(self, start: str, end: str) -> None:
        """Add a simple edge between two nodes.

        Args:
            start: Source node name.
            end: Target node name.
        """
        self.edges[start] = end

    def add_conditional_edge(self, start: str, condition: ConditionalDecision) -> None:
        """Add a conditional edge with a decision function.

        The decision function receives the current state and returns
        the name of the next node to execute.

        Args:
            start: Source node name.
            condition: Function that takes State and returns next node name.
        """
        self.conditional_edges[start] = condition

    def run(self, initial_state: State) -> State:
        """Execute the graph starting from entry_point.

        Traverses nodes according to edges and conditional edges
        until no more transitions are available.

        Args:
            initial_state: Starting state for execution.

        Returns:
            Final state after graph execution completes.
        """
        current_node = self.entry_point
        state = initial_state

        while current_node:
            # Execute current node if it exists
            if current_node in self.nodes:
                state = self.nodes[current_node](state)

            # Determine next node
            if current_node in self.conditional_edges:
                # Conditional edge: call decision function
                current_node = self.conditional_edges[current_node](state)
            elif current_node in self.edges:
                # Simple edge: follow to next node
                current_node = self.edges[current_node]
            else:
                # No outgoing edge: terminate
                current_node = ""

        return state
