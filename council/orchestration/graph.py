"""
StateGraph - State Machine Execution Engine for 2026 Architecture.

Implements Pattern B (Stateful Graph) from 2026 AGI Best Practices.
Provides deterministic state transitions with conditional branching.

2026 Enhancements:
- Checkpoint persistence for resumable workflows
- Approval nodes for human-in-the-loop
- Parallel branch execution
- Loop control with max iterations

Usage:
    graph = StateGraph()
    graph.add_node("plan", planner_action)
    graph.add_node("code", coder_action)
    graph.add_edge("plan", "code")
    graph.set_entry_point("plan")
    final_state = await graph.run_async(initial_state)
"""

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Awaitable
from datetime import datetime
from pathlib import Path
from enum import Enum
import asyncio
import json
import logging
import uuid

logger = logging.getLogger(__name__)


class NodeType(Enum):
    """Type of graph node."""
    STANDARD = "standard"
    APPROVAL = "approval"
    PARALLEL = "parallel"
    LOOP = "loop"


@dataclass
class Checkpoint:
    """
    Checkpoint for resumable execution (2026).

    Attributes:
        id: Unique checkpoint identifier
        graph_name: Name of the graph
        current_node: Current node name
        state_data: Serialized state
        timestamp: When checkpoint was created
        metadata: Additional metadata
    """
    id: str
    graph_name: str
    current_node: str
    state_data: Dict[str, Any]
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "id": self.id,
            "graph_name": self.graph_name,
            "current_node": self.current_node,
            "state_data": self.state_data,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Checkpoint":
        """Create from dictionary."""
        return cls(
            id=data["id"],
            graph_name=data["graph_name"],
            current_node=data["current_node"],
            state_data=data["state_data"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            metadata=data.get("metadata", {}),
        )


@dataclass
class State:
    """Shared state passed between graph nodes.

    Attributes:
        messages: List of message dictionaries (role/content pairs).
        context: Arbitrary context data for the workflow.
        next_node: Optional hint for next node (used by conditional edges).
        approved: Whether approval was granted (for approval nodes).
        loop_count: Current loop iteration count.
    """

    messages: List[Dict[str, str]] = field(default_factory=list)
    context: Dict[str, Any] = field(default_factory=dict)
    next_node: Optional[str] = None
    approved: bool = True  # 2026: For approval nodes
    loop_count: int = 0  # 2026: For loop control

    def to_dict(self) -> Dict[str, Any]:
        """Serialize state to dictionary."""
        return {
            "messages": self.messages,
            "context": self.context,
            "next_node": self.next_node,
            "approved": self.approved,
            "loop_count": self.loop_count,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "State":
        """Deserialize state from dictionary."""
        return cls(
            messages=data.get("messages", []),
            context=data.get("context", {}),
            next_node=data.get("next_node"),
            approved=data.get("approved", True),
            loop_count=data.get("loop_count", 0),
        )


# Type alias for node action functions
NodeAction = Callable[[State], State]
AsyncNodeAction = Callable[[State], Awaitable[State]]
# Type alias for conditional edge decision functions
ConditionalDecision = Callable[[State], str]
# Type alias for approval functions
ApprovalFunc = Callable[[State], Awaitable[bool]]


@dataclass
class LoopConfig:
    """Configuration for loop edges."""
    condition: Callable[[State], bool]
    max_iterations: int = 10
    loop_counter_key: str = "loop_count"


@dataclass
class ParallelConfig:
    """Configuration for parallel nodes."""
    nodes: List[str]
    join_node: str
    merge_strategy: str = "all"  # "all", "any", "first"


class StateGraph:
    """
    State machine graph for workflow execution (2026 Enhanced).

    Supports:
    - Linear node chains via add_edge()
    - Conditional branching via add_conditional_edge()
    - Checkpoint persistence via checkpoint()/resume()
    - Approval nodes for human-in-the-loop
    - Parallel execution via add_parallel_nodes()
    - Loop control via add_loop_edge()

    Example:
        >>> graph = StateGraph(name="my_workflow")
        >>> graph.add_node("start", lambda s: s)
        >>> graph.add_approval_node("review", approval_func)
        >>> graph.set_entry_point("start")
        >>> result = await graph.run_async(State())
    """

    def __init__(
        self,
        name: str = "default",
        checkpoint_dir: str = ".council/checkpoints",
    ) -> None:
        """Initialize an empty state graph."""
        self.name = name
        self.checkpoint_dir = Path(checkpoint_dir)

        self.nodes: Dict[str, NodeAction] = {}
        self.async_nodes: Dict[str, AsyncNodeAction] = {}
        self.node_types: Dict[str, NodeType] = {}
        self.edges: Dict[str, str] = {}
        self.conditional_edges: Dict[str, ConditionalDecision] = {}
        self.entry_point: str = ""

        # 2026 enhancements
        self.approval_nodes: Dict[str, ApprovalFunc] = {}
        self.parallel_configs: Dict[str, ParallelConfig] = {}
        self.loop_configs: Dict[str, LoopConfig] = {}
        self._execution_history: List[str] = []

    def add_node(self, name: str, action: NodeAction) -> None:
        """Add a node with an action function."""
        self.nodes[name] = action
        self.node_types[name] = NodeType.STANDARD

    def add_async_node(self, name: str, action: AsyncNodeAction) -> None:
        """Add an async node with an action function."""
        self.async_nodes[name] = action
        self.node_types[name] = NodeType.STANDARD

    def set_entry_point(self, name: str) -> None:
        """Set the starting node for graph execution."""
        self.entry_point = name

    def add_edge(self, start: str, end: str) -> None:
        """Add a simple edge between two nodes."""
        self.edges[start] = end

    def add_conditional_edge(self, start: str, condition: ConditionalDecision) -> None:
        """Add a conditional edge with a decision function."""
        self.conditional_edges[start] = condition

    # ========== 2026 Enhancements ==========

    def add_approval_node(
        self,
        name: str,
        approval_func: Optional[ApprovalFunc] = None,
        timeout: float = 300.0,
    ) -> None:
        """
        Add a human approval node (2026).

        The workflow pauses at this node until approval is granted.

        Args:
            name: Node name
            approval_func: Async function that returns True if approved
            timeout: Maximum wait time in seconds
        """
        async def default_approval(state: State) -> bool:
            logger.info(f"Approval required at node: {name}")
            logger.info(f"Context: {state.context}")
            # In production, this would wait for user input
            return True

        self.approval_nodes[name] = approval_func or default_approval
        self.node_types[name] = NodeType.APPROVAL

        # Add a simple pass-through action
        async def approval_action(state: State) -> State:
            approved = await self.approval_nodes[name](state)
            state.approved = approved
            if not approved:
                logger.warning(f"Approval denied at node: {name}")
            return state

        self.async_nodes[name] = approval_action

    def add_parallel_nodes(
        self,
        name: str,
        nodes: List[str],
        join_node: str,
        merge_strategy: str = "all",
    ) -> None:
        """
        Add parallel execution nodes (2026).

        Args:
            name: Name for this parallel group
            nodes: List of node names to execute in parallel
            join_node: Node to continue to after all parallel nodes complete
            merge_strategy: How to merge results ("all", "any", "first")
        """
        self.parallel_configs[name] = ParallelConfig(
            nodes=nodes,
            join_node=join_node,
            merge_strategy=merge_strategy,
        )
        self.node_types[name] = NodeType.PARALLEL

    def add_loop_edge(
        self,
        start: str,
        end: str,
        condition: Callable[[State], bool],
        max_iterations: int = 10,
    ) -> None:
        """
        Add a loop edge (2026).

        Loops from start to end while condition is True.

        Args:
            start: Starting node of loop
            end: Node to loop back to
            condition: Function that returns True to continue looping
            max_iterations: Maximum loop iterations
        """
        self.loop_configs[start] = LoopConfig(
            condition=condition,
            max_iterations=max_iterations,
        )

        # Create conditional edge for loop
        def loop_decision(state: State) -> str:
            config = self.loop_configs[start]
            if state.loop_count >= config.max_iterations:
                logger.warning(f"Max iterations reached at {start}")
                return self.edges.get(start, "")

            if config.condition(state):
                state.loop_count += 1
                return end
            else:
                return self.edges.get(start, "")

        self.conditional_edges[start] = loop_decision

    def checkpoint(self, state: State, node: str) -> str:
        """
        Save checkpoint for resumable execution (2026).

        Args:
            state: Current state
            node: Current node name

        Returns:
            Checkpoint ID
        """
        checkpoint_id = f"{self.name}_{node}_{uuid.uuid4().hex[:8]}"
        checkpoint = Checkpoint(
            id=checkpoint_id,
            graph_name=self.name,
            current_node=node,
            state_data=state.to_dict(),
        )

        # Ensure directory exists
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)
        checkpoint_path = self.checkpoint_dir / f"{checkpoint_id}.json"
        checkpoint_path.write_text(json.dumps(checkpoint.to_dict(), indent=2))

        logger.info(f"Checkpoint saved: {checkpoint_id}")
        return checkpoint_id

    def resume(self, checkpoint_id: str) -> tuple[State, str]:
        """
        Resume from checkpoint (2026).

        Args:
            checkpoint_id: ID of checkpoint to resume from

        Returns:
            Tuple of (restored state, node to continue from)
        """
        checkpoint_path = self.checkpoint_dir / f"{checkpoint_id}.json"
        if not checkpoint_path.exists():
            raise FileNotFoundError(f"Checkpoint not found: {checkpoint_id}")

        data = json.loads(checkpoint_path.read_text())
        checkpoint = Checkpoint.from_dict(data)

        state = State.from_dict(checkpoint.state_data)
        logger.info(f"Resumed from checkpoint: {checkpoint_id} at node {checkpoint.current_node}")

        return state, checkpoint.current_node

    def list_checkpoints(self) -> List[Checkpoint]:
        """List all available checkpoints."""
        checkpoints = []
        if self.checkpoint_dir.exists():
            for path in self.checkpoint_dir.glob("*.json"):
                try:
                    data = json.loads(path.read_text())
                    checkpoints.append(Checkpoint.from_dict(data))
                except Exception as e:
                    logger.warning(f"Failed to load checkpoint {path}: {e}")
        return sorted(checkpoints, key=lambda c: c.timestamp, reverse=True)

    def clear_checkpoints(self) -> int:
        """Clear all checkpoints. Returns number cleared."""
        count = 0
        if self.checkpoint_dir.exists():
            for path in self.checkpoint_dir.glob("*.json"):
                path.unlink()
                count += 1
        return count

    async def _execute_node(self, name: str, state: State) -> State:
        """Execute a single node (sync or async)."""
        if name in self.async_nodes:
            return await self.async_nodes[name](state)
        elif name in self.nodes:
            return self.nodes[name](state)
        else:
            logger.warning(f"Node not found: {name}")
            return state

    async def _execute_parallel(self, config: ParallelConfig, state: State) -> State:
        """Execute parallel nodes and merge results."""
        tasks = []
        for node_name in config.nodes:
            # Create a copy of state for each parallel branch
            branch_state = State.from_dict(state.to_dict())
            tasks.append(self._execute_node(node_name, branch_state))

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Merge results based on strategy
        if config.merge_strategy == "all":
            # Merge all contexts
            for result in results:
                if isinstance(result, State):
                    state.context.update(result.context)
                    state.messages.extend(result.messages)
        elif config.merge_strategy == "first":
            # Use first successful result
            for result in results:
                if isinstance(result, State):
                    return result
        elif config.merge_strategy == "any":
            # Return if any succeeded
            for result in results:
                if isinstance(result, State) and result.approved:
                    return result

        return state

    async def run_async(
        self,
        initial_state: State,
        checkpoint_interval: int = 0,
    ) -> State:
        """
        Execute the graph asynchronously (2026).

        Args:
            initial_state: Starting state
            checkpoint_interval: Save checkpoint every N nodes (0 = disabled)

        Returns:
            Final state after execution
        """
        current_node = self.entry_point
        state = initial_state
        step_count = 0

        self._execution_history = []

        while current_node:
            self._execution_history.append(current_node)
            step_count += 1

            # Handle different node types
            node_type = self.node_types.get(current_node, NodeType.STANDARD)

            if node_type == NodeType.PARALLEL and current_node in self.parallel_configs:
                config = self.parallel_configs[current_node]
                state = await self._execute_parallel(config, state)
                current_node = config.join_node
                continue

            # Execute node
            state = await self._execute_node(current_node, state)

            # Check approval for approval nodes
            if node_type == NodeType.APPROVAL and not state.approved:
                logger.warning(f"Execution halted at approval node: {current_node}")
                break

            # Save checkpoint if enabled
            if checkpoint_interval > 0 and step_count % checkpoint_interval == 0:
                self.checkpoint(state, current_node)

            # Determine next node
            if current_node in self.conditional_edges:
                current_node = self.conditional_edges[current_node](state)
            elif current_node in self.edges:
                current_node = self.edges[current_node]
            else:
                current_node = ""

        return state

    def run(self, initial_state: State) -> State:
        """Execute the graph synchronously (legacy support)."""
        current_node = self.entry_point
        state = initial_state

        while current_node:
            # Execute current node if it exists
            if current_node in self.nodes:
                state = self.nodes[current_node](state)

            # Determine next node
            if current_node in self.conditional_edges:
                current_node = self.conditional_edges[current_node](state)
            elif current_node in self.edges:
                current_node = self.edges[current_node]
            else:
                current_node = ""

        return state

    def get_execution_history(self) -> List[str]:
        """Get list of executed nodes (2026)."""
        return self._execution_history.copy()

    def visualize(self) -> str:
        """
        Generate Mermaid diagram of the graph (2026).

        Returns:
            Mermaid diagram string
        """
        lines = ["graph TD"]

        # Add nodes
        for name, node_type in self.node_types.items():
            if node_type == NodeType.APPROVAL:
                lines.append(f"    {name}[/{name}/]")  # Diamond shape
            elif node_type == NodeType.PARALLEL:
                lines.append(f"    {name}[[\"{name}\"]]")  # Stadium shape
            else:
                lines.append(f"    {name}[{name}]")

        # Add edges
        for start, end in self.edges.items():
            lines.append(f"    {start} --> {end}")

        # Add conditional edges (as dashed)
        for start in self.conditional_edges:
            lines.append(f"    {start} -.-> |condition| ...")

        # Add parallel configs
        for name, config in self.parallel_configs.items():
            for node in config.nodes:
                lines.append(f"    {name} --> {node}")
            lines.append(f"    {config.nodes[-1]} --> {config.join_node}")

        return "\n".join(lines)
