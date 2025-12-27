"""
TDD Tests for OrchestratorAgent
RED Phase: These tests should FAIL until OrchestratorAgent is implemented.
"""

import unittest
from council.orchestration.hub import Hub
from council.orchestration.events import EventType
from council.orchestration.ledger import DualLedger


class TestOrchestratorAgent(unittest.TestCase):
    """Tests for OrchestratorAgent."""

    def setUp(self):
        self.ledger = DualLedger.create(
            task_id="ORCH-TEST", goal="Orchestrator Testing"
        )
        self.hub = Hub(ledger=self.ledger)

    def test_orchestrator_has_supervisor_role(self):
        """OrchestratorAgent should have supervisor role."""
        from council.agents.orchestrator_hub import OrchestratorAgent

        orch = OrchestratorAgent(name="orch", role="supervisor", hub=self.hub)
        self.assertEqual(orch.role, "supervisor")

    def test_orchestrator_can_dispatch_task(self):
        """OrchestratorAgent should dispatch tasks to appropriate agents."""
        from council.agents.orchestrator_hub import OrchestratorAgent

        orch = OrchestratorAgent(name="orch", role="supervisor", hub=self.hub)
        orch.dispatch("Implement user login")

        events = self.hub.get_recent_events()
        task_events = [e for e in events if e.type == EventType.TASK_CREATED]
        self.assertGreater(len(task_events), 0)

    def test_orchestrator_monitors_progress(self):
        """OrchestratorAgent should monitor Hub events."""
        from council.agents.orchestrator_hub import OrchestratorAgent

        OrchestratorAgent(name="orch", role="supervisor", hub=self.hub)
        self.assertIn(EventType.TEST_PASSED, self.hub._subscribers)
        self.assertIn(EventType.TEST_FAILED, self.hub._subscribers)

    def test_orchestrator_calculates_wald_score(self):
        """OrchestratorAgent should calculate Wald Score for decision."""
        from council.agents.orchestrator_hub import OrchestratorAgent

        orch = OrchestratorAgent(name="orch", role="supervisor", hub=self.hub)
        score = orch.get_wald_score()
        self.assertGreaterEqual(score, 0.0)
        self.assertLessEqual(score, 1.0)


if __name__ == "__main__":
    unittest.main()
