"""
TDD Tests for PlannerAgent
RED Phase: These tests should FAIL until PlannerAgent is implemented.
"""

import unittest
from council.orchestration.hub import Hub
from council.orchestration.events import EventType
from council.orchestration.ledger import DualLedger


class TestPlannerAgent(unittest.TestCase):
    """Tests for PlannerAgent."""

    def setUp(self):
        self.ledger = DualLedger.create(task_id="PLANNER-TEST", goal="Planner Test")
        self.hub = Hub(ledger=self.ledger)

    def test_planner_can_decompose_goal(self):
        """PlannerAgent should decompose a goal into subtasks."""
        from council.agents.planner_hub import PlannerAgent

        planner = PlannerAgent(name="planner", role="task_planner", hub=self.hub)

        # Decompose a goal
        subtasks = planner.decompose("Implement user authentication")

        self.assertIsInstance(subtasks, list)
        self.assertGreater(len(subtasks), 0)

    def test_planner_publishes_task_created_events(self):
        """PlannerAgent should publish TASK_CREATED for each subtask."""
        from council.agents.planner_hub import PlannerAgent

        planner = PlannerAgent(name="planner", role="task_planner", hub=self.hub)

        # Decompose and publish
        planner.plan_and_publish("Implement user authentication")

        # Verify TASK_CREATED events were published
        events = self.hub.get_recent_events()
        task_events = [e for e in events if e.type == EventType.TASK_CREATED]
        self.assertGreater(len(task_events), 0)

    def test_planner_has_planning_capabilities(self):
        """PlannerAgent should have planning capabilities."""
        from council.agents.planner_hub import PlannerAgent

        planner = PlannerAgent(name="planner", role="task_planner", hub=self.hub)

        self.assertIn("decompose_goal", planner.capabilities)
        self.assertIn("prioritize", planner.capabilities)


if __name__ == "__main__":
    unittest.main()
