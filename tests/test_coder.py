"""
TDD Tests for CoderAgent
RED Phase: These tests should FAIL until CoderAgent is implemented.
"""

import unittest
from council.orchestration.hub import Hub
from council.orchestration.events import Event, EventType
from council.orchestration.ledger import DualLedger


class TestCoderAgent(unittest.TestCase):
    """Tests for CoderAgent."""

    def setUp(self):
        self.ledger = DualLedger.create(task_id="CODER-TEST", goal="Coder Testing")
        self.hub = Hub(ledger=self.ledger)

    def test_coder_subscribes_to_task_created(self):
        """CoderAgent should subscribe to TASK_CREATED events."""
        from council.agents.coder_hub import CoderAgent

        CoderAgent(name="coder", role="code_writer", hub=self.hub)

        # Mock: track subscription
        self.assertIn(EventType.TASK_CREATED, self.hub._subscribers)

    def test_coder_publishes_code_written_on_task(self):
        """CoderAgent should publish CODE_WRITTEN when receiving a task."""
        from council.agents.coder_hub import CoderAgent

        CoderAgent(name="coder", role="code_writer", hub=self.hub)

        # Simulate task event
        task_event = Event(
            type=EventType.TASK_CREATED,
            source="planner",
            payload={"task": "implement login", "file": "login.py"},
        )
        self.hub.publish(task_event)

        # Verify CODE_WRITTEN was published
        events = self.hub.get_recent_events()
        event_types = [e.type for e in events]
        self.assertIn(EventType.CODE_WRITTEN, event_types)

    def test_coder_has_code_capabilities(self):
        """CoderAgent should have coding capabilities."""
        from council.agents.coder_hub import CoderAgent

        coder = CoderAgent(name="coder", role="code_writer", hub=self.hub)

        self.assertIn("write_code", coder.capabilities)
        self.assertIn("refactor", coder.capabilities)


if __name__ == "__main__":
    unittest.main()
