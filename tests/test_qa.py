"""
TDD Tests for QAAgent
RED Phase: These tests should FAIL until QAAgent is implemented.
"""

import unittest
from council.orchestration.hub import Hub
from council.orchestration.events import Event, EventType
from council.orchestration.ledger import DualLedger


class TestQAAgent(unittest.TestCase):
    """Tests for QAAgent."""

    def setUp(self):
        self.ledger = DualLedger.create(task_id="QA-TEST", goal="QA Testing")
        self.hub = Hub(ledger=self.ledger)

    def test_qa_subscribes_to_code_written(self):
        """QAAgent should subscribe to CODE_WRITTEN events."""
        from council.agents.qa_hub import QAAgent

        QAAgent(name="qa", role="tester", hub=self.hub)
        self.assertIn(EventType.CODE_WRITTEN, self.hub._subscribers)

    def test_qa_publishes_test_passed_on_code(self):
        """QAAgent should publish TEST_PASSED when code passes tests."""
        from council.agents.qa_hub import QAAgent

        QAAgent(name="qa", role="tester", hub=self.hub)
        code_event = Event(
            type=EventType.CODE_WRITTEN,
            source="coder",
            payload={"file": "login.py", "lines": 50},
        )
        self.hub.publish(code_event)

        events = self.hub.get_recent_events()
        event_types = [e.type for e in events]
        self.assertIn(EventType.TEST_PASSED, event_types)

    def test_qa_has_test_capabilities(self):
        """QAAgent should have testing capabilities."""
        from council.agents.qa_hub import QAAgent

        qa = QAAgent(name="qa", role="tester", hub=self.hub)
        self.assertIn("run_tests", qa.capabilities)
        self.assertIn("lint", qa.capabilities)


if __name__ == "__main__":
    unittest.main()
