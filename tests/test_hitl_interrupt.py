"""
Tests for HITL interrupt/resume flow.
"""

import unittest

from council.orchestration.hub import Hub
from council.orchestration.ledger import DualLedger


class TestHITLInterrupt(unittest.TestCase):
    def setUp(self):
        self.ledger = DualLedger.create(task_id="HITL-INT", goal="Interrupt testing")
        self.hub = Hub(ledger=self.ledger)

    def test_interrupt_raises_and_resumes(self):
        from council.agents.hitl import HITLGate, HumanInterrupt, InterruptStatus

        gate = HITLGate(hub=self.hub)
        action = {"type": "DELETE_FILE", "target": "important.py", "risk": "high"}

        with self.assertRaises(HumanInterrupt) as ctx:
            gate.interrupt(action, state={"step": "pending"})

        record = ctx.exception.record
        self.assertEqual(record.status, InterruptStatus.PENDING)

        resumed = gate.resume(
            record.approval_id,
            approved=True,
            approver="tester",
            resume_payload={"ok": True},
        )
        self.assertEqual(resumed.status, InterruptStatus.APPROVED)
        self.assertEqual(resumed.resume_payload, {"ok": True})

    def test_interrupt_rejects(self):
        from council.agents.hitl import HITLGate, HumanInterrupt, InterruptStatus

        gate = HITLGate(hub=self.hub)
        action = {"type": "DEPLOY", "target": "prod", "risk": "high"}

        with self.assertRaises(HumanInterrupt) as ctx:
            gate.interrupt(action)

        record = ctx.exception.record
        resumed = gate.resume(
            record.approval_id,
            approved=False,
            approver="reviewer",
            reason="Not ready",
        )
        self.assertEqual(resumed.status, InterruptStatus.REJECTED)


if __name__ == "__main__":
    unittest.main()
