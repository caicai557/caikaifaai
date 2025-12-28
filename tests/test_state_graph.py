#!/usr/bin/env python3
"""
TDD Tests for StateGraph - State Machine Execution Engine.

Acceptance Criteria:
- AC1: council/orchestration/graph.py 实现 StateGraph 类
- AC2: StateGraph 支持条件边和状态转换
- AC5: just verify 全部通过
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestState:
    """Tests for State dataclass."""

    def test_state_creation_with_defaults(self):
        """Test State can be created with default values."""
        from council.orchestration.graph import State

        state = State(messages=[], context={})

        assert state.messages == []
        assert state.context == {}
        assert state.next_node is None

    def test_state_creation_with_data(self):
        """Test State can be created with data."""
        from council.orchestration.graph import State

        messages = [{"role": "user", "content": "hello"}]
        context = {"step": 1, "status": "running"}

        state = State(messages=messages, context=context, next_node="process")

        assert state.messages == messages
        assert state.context == context
        assert state.next_node == "process"

    def test_state_is_mutable(self):
        """Test State context can be modified during execution."""
        from council.orchestration.graph import State

        state = State(messages=[], context={"counter": 0})
        state.context["counter"] = 1
        state.messages.append({"role": "system", "content": "updated"})

        assert state.context["counter"] == 1
        assert len(state.messages) == 1


class TestStateGraphCreation:
    """Tests for StateGraph initialization."""

    def test_state_graph_creation(self):
        """Test StateGraph can be instantiated."""
        from council.orchestration.graph import StateGraph

        graph = StateGraph()

        assert graph.nodes == {}
        assert graph.edges == {}
        assert graph.conditional_edges == {}
        assert graph.entry_point == ""

    def test_set_entry_point(self):
        """Test setting the entry point."""
        from council.orchestration.graph import StateGraph

        graph = StateGraph()
        graph.set_entry_point("start")

        assert graph.entry_point == "start"


class TestStateGraphNodeManagement:
    """Tests for adding nodes to StateGraph."""

    def test_add_node(self):
        """Test adding a node with an action function."""
        from council.orchestration.graph import StateGraph, State

        def action(state: State) -> State:
            state.context["processed"] = True
            return state

        graph = StateGraph()
        graph.add_node("process", action)

        assert "process" in graph.nodes
        assert graph.nodes["process"] == action

    def test_add_multiple_nodes(self):
        """Test adding multiple nodes."""
        from council.orchestration.graph import StateGraph, State

        def action1(state: State) -> State:
            return state

        def action2(state: State) -> State:
            return state

        graph = StateGraph()
        graph.add_node("step1", action1)
        graph.add_node("step2", action2)

        assert len(graph.nodes) == 2
        assert "step1" in graph.nodes
        assert "step2" in graph.nodes


class TestStateGraphEdges:
    """Tests for adding edges to StateGraph."""

    def test_add_edge(self):
        """Test adding a simple edge between nodes."""
        from council.orchestration.graph import StateGraph

        graph = StateGraph()
        graph.add_edge("start", "end")

        assert graph.edges["start"] == "end"

    def test_add_conditional_edge(self):
        """Test adding a conditional edge with a decision function."""
        from council.orchestration.graph import StateGraph, State

        def decide(state: State) -> str:
            return "yes" if state.context.get("flag") else "no"

        graph = StateGraph()
        graph.add_conditional_edge("check", decide)

        assert "check" in graph.conditional_edges
        assert graph.conditional_edges["check"] == decide


class TestStateGraphExecution:
    """Tests for StateGraph.run() execution engine."""

    def test_run_single_node(self):
        """Test running a graph with a single node."""
        from council.orchestration.graph import StateGraph, State

        def action(state: State) -> State:
            state.context["executed"] = True
            return state

        graph = StateGraph()
        graph.add_node("start", action)
        graph.set_entry_point("start")

        initial_state = State(messages=[], context={})
        final_state = graph.run(initial_state)

        assert final_state.context["executed"] is True

    def test_run_linear_graph(self):
        """Test running a linear graph with multiple nodes."""
        from council.orchestration.graph import StateGraph, State

        def step1(state: State) -> State:
            state.context["steps"] = [1]
            return state

        def step2(state: State) -> State:
            state.context["steps"].append(2)
            return state

        def step3(state: State) -> State:
            state.context["steps"].append(3)
            return state

        graph = StateGraph()
        graph.add_node("step1", step1)
        graph.add_node("step2", step2)
        graph.add_node("step3", step3)
        graph.add_edge("step1", "step2")
        graph.add_edge("step2", "step3")
        graph.set_entry_point("step1")

        initial_state = State(messages=[], context={})
        final_state = graph.run(initial_state)

        assert final_state.context["steps"] == [1, 2, 3]

    def test_run_with_conditional_edge(self):
        """Test running a graph with conditional branching."""
        from council.orchestration.graph import StateGraph, State

        def check(state: State) -> State:
            # Just pass through, decision is made by conditional edge
            return state

        def decide(state: State) -> str:
            return "success" if state.context.get("valid") else "failure"

        def on_success(state: State) -> State:
            state.context["result"] = "passed"
            return state

        def on_failure(state: State) -> State:
            state.context["result"] = "failed"
            return state

        graph = StateGraph()
        graph.add_node("check", check)
        graph.add_node("success", on_success)
        graph.add_node("failure", on_failure)
        graph.add_conditional_edge("check", decide)
        graph.set_entry_point("check")

        # Test success path
        state_valid = State(messages=[], context={"valid": True})
        result_valid = graph.run(state_valid)
        assert result_valid.context["result"] == "passed"

        # Test failure path
        state_invalid = State(messages=[], context={"valid": False})
        result_invalid = graph.run(state_invalid)
        assert result_invalid.context["result"] == "failed"

    def test_run_terminates_at_end(self):
        """Test graph execution terminates when no more edges."""
        from council.orchestration.graph import StateGraph, State

        execution_count = {"value": 0}

        def action(state: State) -> State:
            execution_count["value"] += 1
            return state

        graph = StateGraph()
        graph.add_node("only", action)
        graph.set_entry_point("only")

        initial_state = State(messages=[], context={})
        graph.run(initial_state)

        assert execution_count["value"] == 1

    def test_run_empty_graph_returns_initial_state(self):
        """Test running an empty graph returns initial state unchanged."""
        from council.orchestration.graph import StateGraph, State

        graph = StateGraph()
        # No entry point set, graph is empty

        initial_state = State(messages=[{"test": "data"}], context={"key": "value"})
        final_state = graph.run(initial_state)

        assert final_state.messages == initial_state.messages
        assert final_state.context == initial_state.context


class TestStateGraphIntegration:
    """Integration tests for StateGraph with complex workflows."""

    def test_multi_step_workflow_with_messages(self):
        """Test a workflow that processes and transforms messages."""
        from council.orchestration.graph import StateGraph, State

        def receive(state: State) -> State:
            state.messages.append({"role": "user", "content": "input"})
            return state

        def process(state: State) -> State:
            state.context["processed"] = True
            return state

        def respond(state: State) -> State:
            state.messages.append({"role": "assistant", "content": "output"})
            return state

        graph = StateGraph()
        graph.add_node("receive", receive)
        graph.add_node("process", process)
        graph.add_node("respond", respond)
        graph.add_edge("receive", "process")
        graph.add_edge("process", "respond")
        graph.set_entry_point("receive")

        initial_state = State(messages=[], context={})
        final_state = graph.run(initial_state)

        assert len(final_state.messages) == 2
        assert final_state.messages[0]["role"] == "user"
        assert final_state.messages[1]["role"] == "assistant"
        assert final_state.context["processed"] is True

    def test_loop_detection_via_max_iterations(self):
        """Test that graph can handle potential loops with iteration limit."""
        from council.orchestration.graph import StateGraph, State

        def increment(state: State) -> State:
            state.context["count"] = state.context.get("count", 0) + 1
            return state

        def should_continue(state: State) -> str:
            # Continue until count reaches 5, then stop
            if state.context.get("count", 0) < 5:
                return "loop"
            return "end"

        def end_action(state: State) -> State:
            state.context["done"] = True
            return state

        graph = StateGraph()
        graph.add_node("loop", increment)
        graph.add_node("end", end_action)
        graph.add_conditional_edge("loop", should_continue)
        graph.set_entry_point("loop")

        initial_state = State(messages=[], context={})
        final_state = graph.run(initial_state)

        assert final_state.context["count"] == 5
        assert final_state.context["done"] is True
