"""
TDD Tests for BaseAgent
RED Phase: These tests should FAIL until BaseAgent is implemented.
"""

import unittest
from council.orchestration.hub import Hub
from council.orchestration.events import Event, EventType
from council.orchestration.ledger import DualLedger


class TestBaseAgent(unittest.TestCase):
    """Tests for BaseAgent abstract class."""

    def setUp(self):
        self.ledger = DualLedger.create(task_id="AGENT-TEST", goal="Agent Testing")
        self.hub = Hub(ledger=self.ledger)

    def test_agent_must_have_name_and_role(self):
        """Agent must define name and role."""
        from council.agents.base import BaseAgent

        class TestAgent(BaseAgent):
            def handle_event(self, event: Event) -> None:
                pass

        agent = TestAgent(name="test_agent", role="tester", hub=self.hub)

        self.assertEqual(agent.name, "test_agent")
        self.assertEqual(agent.role, "tester")

    def test_agent_must_connect_to_hub(self):
        """Agent must be connected to a Hub instance."""
        from council.agents.base import BaseAgent

        class TestAgent(BaseAgent):
            def handle_event(self, event: Event) -> None:
                pass

        agent = TestAgent(name="test_agent", role="tester", hub=self.hub)

        self.assertIs(agent.hub, self.hub)

    def test_agent_can_subscribe_to_events(self):
        """Agent can subscribe to event types."""
        from council.agents.base import BaseAgent

        received = []

        class TestAgent(BaseAgent):
            def handle_event(self, event: Event) -> None:
                received.append(event)

        agent = TestAgent(name="listener", role="observer", hub=self.hub)
        agent.subscribe([EventType.HEARTBEAT])

        self.hub.publish(Event(type=EventType.HEARTBEAT, source="system"))

        self.assertEqual(len(received), 1)

    def test_agent_can_publish_events(self):
        """Agent can publish events to Hub."""
        from council.agents.base import BaseAgent

        class TestAgent(BaseAgent):
            def handle_event(self, event: Event) -> None:
                pass

        agent = TestAgent(name="publisher", role="sender", hub=self.hub)
        agent.publish(Event(type=EventType.TASK_CREATED, source=agent.name))

        self.assertEqual(len(self.hub.get_recent_events()), 1)
        self.assertEqual(self.hub.get_recent_events()[0].type, EventType.TASK_CREATED)

    def test_agent_has_capabilities_list(self):
        """Agent should have a list of capabilities."""
        from council.agents.base import BaseAgent

        class TestAgent(BaseAgent):
            def handle_event(self, event: Event) -> None:
                pass

        agent = TestAgent(
            name="skilled",
            role="worker",
            hub=self.hub,
            capabilities=["read", "write", "execute"],
        )

        self.assertEqual(agent.capabilities, ["read", "write", "execute"])

    def test_agent_default_capabilities_empty(self):
        """Agent default capabilities should be empty list."""
        from council.agents.base import BaseAgent

        class TestAgent(BaseAgent):
            def handle_event(self, event: Event) -> None:
                pass

        agent = TestAgent(name="basic", role="worker", hub=self.hub)

        self.assertEqual(agent.capabilities, [])


if __name__ == "__main__":
    unittest.main()
