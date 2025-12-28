"""
Integration Test - Full Agent Workflow
Tests: Planner → Coder → QA → Orchestrator decision
"""

import unittest
import logging
from council.orchestration.hub import Hub
from council.orchestration.events import Event, EventType
from council.orchestration.ledger import DualLedger

from council.agents.planner_hub import PlannerAgent
from council.agents.coder_hub import CoderAgent
from council.agents.qa_hub import QAAgent
from council.agents.orchestrator_hub import OrchestratorAgent

# Enable logging for visibility
logging.basicConfig(level=logging.INFO)


class TestAgentIntegration(unittest.TestCase):
    """End-to-end integration tests for Agent Council."""

    def setUp(self):
        self.ledger = DualLedger.create(
            task_id="INTEGRATION-TEST", goal="Full Workflow"
        )
        self.hub = Hub(ledger=self.ledger)

    def test_full_workflow_plan_code_qa(self):
        """
        Scenario: Plan → Code → QA
        1. Planner decomposes goal
        2. Coder picks up task
        3. QA runs tests
        """
        # Initialize agents
        planner = PlannerAgent(name="planner", role="planner", hub=self.hub)
        CoderAgent(name="coder", role="coder", hub=self.hub)
        QAAgent(name="qa", role="qa", hub=self.hub)
        orch = OrchestratorAgent(name="orch", role="supervisor", hub=self.hub)

        # Planner creates tasks
        planner.plan_and_publish("Implement login feature")

        # Verify event chain
        events = self.hub.get_recent_events()
        event_types = [e.type for e in events]

        # Should have: TASK_CREATED → CODE_WRITTEN → TEST_PASSED
        self.assertIn(EventType.TASK_CREATED, event_types)
        self.assertIn(EventType.CODE_WRITTEN, event_types)
        self.assertIn(EventType.TEST_PASSED, event_types)

        # Orchestrator should have recorded a success
        self.assertGreater(orch._success_count, 0)

    def test_orchestrator_wald_decision(self):
        """
        Scenario: Orchestrator decides based on Wald Score
        """
        orch = OrchestratorAgent(name="orch", role="supervisor", hub=self.hub)

        # Simulate multiple successes
        for _ in range(10):
            self.hub.publish(Event(type=EventType.TEST_PASSED, source="qa", payload={}))

        # Wald score should be high
        self.assertGreaterEqual(orch.get_wald_score(), 0.9)
        self.assertTrue(orch.should_commit())

    def test_ledger_updates_via_events(self):
        """
        Scenario: Ledger should be updated via Hub events
        """
        CoderAgent(name="coder", role="coder", hub=self.hub)
        QAAgent(name="qa", role="qa", hub=self.hub)

        # Trigger a task
        self.hub.publish(
            Event(
                type=EventType.TASK_CREATED,
                source="planner",
                payload={"task": "test task", "file": "test.py"},
            )
        )

        # Ledger should have recorded iterations
        self.assertGreater(len(self.ledger.progress.iterations), 0)


if __name__ == "__main__":
    unittest.main()
