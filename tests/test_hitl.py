"""
TDD Tests for Human-in-the-Loop (HITL) Hook
RED Phase: Tests for HITL decision gating.
"""

import unittest
from council.orchestration.hub import Hub
from council.orchestration.ledger import DualLedger


class TestHITL(unittest.TestCase):
    """Tests for Human-in-the-Loop functionality."""

    def setUp(self):
        self.ledger = DualLedger.create(task_id="HITL-TEST", goal="HITL Testing")
        self.hub = Hub(ledger=self.ledger)

    def test_hitl_hook_blocks_high_risk_action(self):
        """High-risk actions should be blocked pending human approval."""
        from council.agents.hitl import HITLGate

        gate = HITLGate(hub=self.hub)

        # Simulate high-risk action
        action = {"type": "DELETE_FILE", "target": "important.py", "risk": "high"}

        # Should be blocked
        result = gate.request_approval(action)
        self.assertEqual(result.status, "PENDING")
        self.assertFalse(result.approved)

    def test_hitl_approves_low_risk_action(self):
        """Low-risk actions should be auto-approved."""
        from council.agents.hitl import HITLGate

        gate = HITLGate(hub=self.hub, auto_approve_low_risk=True)

        # Simulate low-risk action
        action = {"type": "READ_FILE", "target": "readme.md", "risk": "low"}

        result = gate.request_approval(action)
        self.assertEqual(result.status, "AUTO_APPROVED")
        self.assertTrue(result.approved)

    def test_hitl_publishes_approval_request_event(self):
        """HITL should publish APPROVAL_REQUESTED event."""
        from council.agents.hitl import HITLGate

        gate = HITLGate(hub=self.hub)

        action = {"type": "DEPLOY", "target": "production", "risk": "high"}
        gate.request_approval(action)

        # Verify event published
        events = self.hub.get_recent_events()
        # Check if any event contains approval request info
        self.assertGreater(len(events), 0)


if __name__ == "__main__":
    unittest.main()
