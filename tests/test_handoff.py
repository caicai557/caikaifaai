"""
Tests for council/orchestration/handoff.py
"""

from council.orchestration.handoff import (
    AgentHandoff,
    ContextSnapshot,
    HandoffManager,
    HandoffPriority,
    HandoffStatus,
)


class TestContextSnapshot:
    """Tests for ContextSnapshot"""

    def test_create_snapshot(self):
        """Test creating a context snapshot"""
        snapshot = ContextSnapshot(task_summary="Implement login feature")
        assert snapshot.task_summary == "Implement login feature"
        assert snapshot.recent_decisions == []
        assert snapshot.key_facts == {}

    def test_add_decision_bounded(self):
        """Test that decisions are bounded by max_items"""
        snapshot = ContextSnapshot(task_summary="Test", max_items=3)
        for i in range(5):
            snapshot.add_decision(f"Decision {i}")
        assert len(snapshot.recent_decisions) == 3
        assert snapshot.recent_decisions[0] == "Decision 2"

    def test_to_prompt(self):
        """Test converting to prompt string"""
        snapshot = ContextSnapshot(task_summary="Build API")
        snapshot.add_decision("Use FastAPI")
        snapshot.add_fact("language", "Python")
        snapshot.constraints.append("Must be async")

        prompt = snapshot.to_prompt()
        assert "Build API" in prompt
        assert "Use FastAPI" in prompt
        assert "Python" in prompt
        assert "async" in prompt


class TestAgentHandoff:
    """Tests for AgentHandoff"""

    def test_create_handoff(self):
        """Test creating a handoff"""
        context = ContextSnapshot(task_summary="Test task")
        handoff = AgentHandoff(
            from_agent="Orchestrator",
            to_agent="Coder",
            context=context,
            reason="Needs implementation",
        )
        assert handoff.from_agent == "Orchestrator"
        assert handoff.to_agent == "Coder"
        assert handoff.status == HandoffStatus.PENDING

    def test_handoff_lifecycle(self):
        """Test handoff accept -> complete lifecycle"""
        context = ContextSnapshot(task_summary="Test")
        handoff = AgentHandoff(
            from_agent="A",
            to_agent="B",
            context=context,
            reason="Test",
        )

        assert handoff.status == HandoffStatus.PENDING
        handoff.accept()
        assert handoff.status == HandoffStatus.ACCEPTED
        handoff.complete("Done successfully")
        assert handoff.status == HandoffStatus.COMPLETED
        assert handoff.result == "Done successfully"
        assert handoff.completed_at is not None

    def test_handoff_reject(self):
        """Test handoff rejection"""
        context = ContextSnapshot(task_summary="Test")
        handoff = AgentHandoff(
            from_agent="A",
            to_agent="B",
            context=context,
            reason="Test",
        )
        handoff.reject("Agent busy")
        assert handoff.status == HandoffStatus.REJECTED
        assert handoff.error == "Agent busy"


class TestHandoffManager:
    """Tests for HandoffManager"""

    def test_initiate_handoff(self):
        """Test initiating a handoff"""
        manager = HandoffManager()
        handoff = manager.initiate_handoff(
            from_agent="Orchestrator",
            to_agent="Coder",
            task_summary="Implement feature X",
            reason="Coder specialization needed",
        )

        assert handoff.from_agent == "Orchestrator"
        assert handoff.to_agent == "Coder"
        assert handoff in manager._pending

    def test_priority_ordering(self):
        """Test that handoffs are ordered by priority"""
        manager = HandoffManager()

        # Add low priority first
        h_low = manager.initiate_handoff(
            from_agent="A",
            to_agent="B",
            task_summary="Low",
            reason="Test",
            priority=HandoffPriority.LOW,
        )

        # Add critical priority second
        h_critical = manager.initiate_handoff(
            from_agent="A",
            to_agent="C",
            task_summary="Critical",
            reason="Test",
            priority=HandoffPriority.CRITICAL,
        )

        # Critical should be first in pending list
        assert manager._pending[0] == h_critical
        assert manager._pending[1] == h_low

    def test_complete_handoff(self):
        """Test completing a handoff"""
        manager = HandoffManager()
        handoff = manager.initiate_handoff(
            from_agent="A",
            to_agent="B",
            task_summary="Test",
            reason="Test",
        )

        manager.complete_handoff(handoff, "Result")
        assert handoff not in manager._pending
        assert handoff in manager._history
        assert handoff.status == HandoffStatus.COMPLETED

    def test_get_pending_for_agent(self):
        """Test filtering pending handoffs by agent"""
        manager = HandoffManager()
        manager.initiate_handoff("A", "Coder", "Task 1", "Test")
        manager.initiate_handoff("B", "Coder", "Task 2", "Test")
        manager.initiate_handoff("C", "Architect", "Task 3", "Test")

        coder_handoffs = manager.get_pending_for_agent("Coder")
        assert len(coder_handoffs) == 2

    def test_register_callback(self):
        """Test callback registration and invocation"""
        manager = HandoffManager()
        received = []

        def callback(handoff):
            received.append(handoff)

        manager.register_callback("Coder", callback)
        handoff = manager.initiate_handoff("A", "Coder", "Test", "Test")

        assert len(received) == 1
        assert received[0] == handoff
