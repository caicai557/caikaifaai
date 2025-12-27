#!/usr/bin/env python3
"""
Unit tests for 2025 Orchestration Layer.
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestTaskLedger:
    """Tests for TaskLedger."""

    def test_add_known_fact(self):
        """Test adding a known fact."""
        from council.orchestration.ledger import TaskLedger

        ledger = TaskLedger(task_id="TEST-001", goal="Test goal")
        ledger.add_fact("framework", "FastAPI")

        assert "framework" in ledger.known_facts
        assert ledger.known_facts["framework"] == "FastAPI"

    def test_add_pending_query(self):
        """Test adding a pending query."""
        from council.orchestration.ledger import TaskLedger

        ledger = TaskLedger(task_id="TEST-001", goal="Test goal")
        ledger.add_query("What is the database schema?")

        assert len(ledger.pending_queries) == 1
        assert ledger.pending_queries[0] == "What is the database schema?"

    def test_resolve_query(self):
        """Test resolving a query moves it to known facts."""
        from council.orchestration.ledger import TaskLedger

        ledger = TaskLedger(task_id="TEST-001", goal="Test goal")
        ledger.add_query("API endpoint?")
        ledger.resolve_query("API endpoint?", "/api/v1/users")

        assert len(ledger.pending_queries) == 0
        assert any("resolved:" in k for k in ledger.known_facts)

    def test_to_context(self):
        """Test context generation."""
        from council.orchestration.ledger import TaskLedger

        ledger = TaskLedger(task_id="TEST-001", goal="Test goal")
        ledger.add_fact("key", "value")
        context = ledger.to_context()

        assert "TASK LEDGER" in context
        assert "Test goal" in context
        assert "key: value" in context


class TestProgressLedger:
    """Tests for ProgressLedger."""

    def test_stagnation_counter_increment(self):
        """Test that stagnation counter increments on no progress."""
        from council.orchestration.ledger import ProgressLedger

        ledger = ProgressLedger()
        ledger.record_iteration(progress=False, action="Impl", result="Failed")
        ledger.record_iteration(progress=False, action="Impl", result="Failed again")

        assert ledger.stagnation_count == 2

    def test_stagnation_reset_on_progress(self):
        """Test that stagnation counter resets when progress is made."""
        from council.orchestration.ledger import ProgressLedger

        ledger = ProgressLedger()
        ledger.record_iteration(progress=False)
        ledger.record_iteration(progress=False)
        ledger.record_iteration(progress=True)

        assert ledger.stagnation_count == 0

    def test_auto_replan_trigger(self):
        """Test that should_replan triggers after max stagnation."""
        from council.orchestration.ledger import ProgressLedger

        ledger = ProgressLedger(max_stagnation=3)

        for _ in range(3):
            ledger.record_iteration(progress=False)

        assert ledger.should_replan() is True

    def test_reflect_5_questions(self):
        """Test 5 core questions reflection."""
        from council.orchestration.ledger import ProgressLedger

        ledger = ProgressLedger()
        ledger.record_iteration(progress=True, action="TDD", result="Created tests")
        reflection = ledger.reflect()

        assert "task_completed" in reflection
        assert "in_loop" in reflection
        assert "stagnant" in reflection
        assert "should_replan" in reflection
        assert "total_iterations" in reflection


class TestDualLedger:
    """Tests for DualLedger."""

    def test_create_dual_ledger(self):
        """Test creating a DualLedger instance."""
        from council.orchestration.ledger import DualLedger

        dual = DualLedger.create(task_id="TEST-001", goal="Test goal")

        assert dual.task.task_id == "TEST-001"
        assert dual.task.goal == "Test goal"
        assert dual.progress.stagnation_count == 0

    def test_full_context(self):
        """Test getting full context from both ledgers."""
        from council.orchestration.ledger import DualLedger

        dual = DualLedger.create(task_id="TEST-001", goal="Test goal")
        dual.task.add_fact("key", "value")
        dual.progress.record_iteration(progress=True, action="Init", result="OK")

        context = dual.get_full_context()

        assert "TASK LEDGER" in context
        assert "PROGRESS LEDGER" in context


class TestAdaptiveRouter:
    """Tests for AdaptiveRouter."""

    def test_low_risk_single_model(self):
        """Test that low risk tasks use single model."""
        from council.orchestration.adaptive_router import AdaptiveRouter, ResponseMode

        router = AdaptiveRouter()
        decision = router.route("fix typo in readme")

        assert decision.mode == ResponseMode.SINGLE_MODEL

    def test_high_risk_full_council(self):
        """Test that high risk tasks use full council."""
        from council.orchestration.adaptive_router import AdaptiveRouter, ResponseMode

        router = AdaptiveRouter()
        decision = router.route("git push to production")

        assert decision.mode == ResponseMode.FULL_COUNCIL

    def test_medium_risk_swarm_verify(self):
        """Test that medium risk tasks use swarm + verify."""
        from council.orchestration.adaptive_router import AdaptiveRouter, ResponseMode

        router = AdaptiveRouter()
        decision = router.route("refactor the authentication module")

        assert decision.mode == ResponseMode.SWARM_VERIFY

    def test_assess_risk_with_context(self):
        """Test risk assessment with additional context."""
        from council.orchestration.adaptive_router import AdaptiveRouter, RiskLevel

        router = AdaptiveRouter()
        risk = router.assess_risk("update config", context="production database")

        assert risk == RiskLevel.HIGH

    def test_explain_decision(self):
        """Test decision explanation."""
        from council.orchestration.adaptive_router import AdaptiveRouter

        router = AdaptiveRouter()
        decision = router.route("add unit tests")
        explanation = router.explain_decision(decision)

        assert "ROUTING DECISION" in explanation
        assert "Risk Level" in explanation
