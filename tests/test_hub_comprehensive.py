"""
Comprehensive Tests for Hub and Event System
"""

import unittest
import logging

from council.orchestration.hub import Hub
from council.orchestration.events import Event, EventType
from council.orchestration.ledger import DualLedger, IterationStatus

# Configure logging to capture output during tests
logging.basicConfig(level=logging.DEBUG)


class TestHubComprehensive(unittest.TestCase):
    def setUp(self):
        self.ledger = DualLedger.create(
            task_id="TEST-COMPREHENSIVE", goal="Robustness Test"
        )
        self.hub = Hub(ledger=self.ledger)

    def test_surgical_room_workflow(self):
        """
        Scenario: The 'Surgical Room' Metaphor
        1. Doctor (Coder) finishes code -> Publishes CODE_WRITTEN
        2. Nurse (QA) sees CODE_WRITTEN -> Runs tests -> Publishes TEST_PASSED
        3. Verify Hub coordinates and Ledger updates
        """
        workflow_log = []

        # Define Agents (Callbacks)
        def nurse_qa_agent(event: Event):
            # Nurse reacts to Code Written
            workflow_log.append(f"Nurse received: {event.type.value}")
            # Simulate QA work
            qa_result = Event(
                type=EventType.TEST_PASSED,
                source="nurse_qa",
                payload={"test_suite": "test_login.py", "passed": True},
            )
            self.hub.publish(qa_result)

        # Subscribe
        self.hub.subscribe(EventType.CODE_WRITTEN, nurse_qa_agent)

        # 1. Doctor acts
        doctor_event = Event(
            type=EventType.CODE_WRITTEN,
            source="doctor_coder",
            payload={"file": "login.py", "lines": 50},
        )
        self.hub.publish(doctor_event)

        # Verify Workflow
        # Nurse should have logged receipt
        # Nurse should have logged receipt
        self.assertIn("Nurse received: artifact.code_written", workflow_log)

        # Hub history should contain both events (Doctor's and Nurse's)
        history_types = [e.type for e in self.hub.get_recent_events()]
        self.assertIn(EventType.CODE_WRITTEN, history_types)
        self.assertIn(EventType.TEST_PASSED, history_types)

        # Verify Ledger Updates
        # We expect 2 iterations: one for Code Written, one for Test Passed
        self.assertEqual(len(self.ledger.progress.iterations), 2)

        # Check Stagnation (Should be 0 because both are progress)
        self.assertEqual(self.ledger.progress.stagnation_count, 0)
        self.assertEqual(
            self.ledger.progress.iterations[-1].status, IterationStatus.PROGRESS
        )

    def test_error_isolation(self):
        """
        Scenario: One subscriber crashes, others must survive.
        """
        results = []

        def crashing_subscriber(event: Event):
            raise ValueError("I crashed!")

        def safe_subscriber(event: Event):
            results.append("I survived")

        self.hub.subscribe(EventType.HEARTBEAT, crashing_subscriber)
        self.hub.subscribe(EventType.HEARTBEAT, safe_subscriber)

        event = Event(type=EventType.HEARTBEAT, source="system")

        # Should not raise exception
        try:
            self.hub.publish(event)
        except Exception as e:
            self.fail(f"Hub.publish raised exception unexpectedly: {e}")

        # Verify safe subscriber ran
        self.assertEqual(results, ["I survived"])

    def test_ledger_stagnation_logic(self):
        """
        Scenario: Verify Ledger tracks stagnation correctly via events.
        """
        # 1. Fail -> Stagnation +1
        fail_event = Event(
            type=EventType.TEST_FAILED, source="qa", payload={"error": "SyntaxError"}
        )
        self.hub.publish(fail_event)

        self.assertEqual(self.ledger.progress.stagnation_count, 1)
        self.assertEqual(
            self.ledger.progress.iterations[-1].status, IterationStatus.STAGNANT
        )

        # 2. Fail again -> Stagnation +2
        self.hub.publish(fail_event)
        self.assertEqual(self.ledger.progress.stagnation_count, 2)

        # 3. Success -> Stagnation Reset
        success_event = Event(
            type=EventType.TEST_PASSED, source="qa", payload={"passed": True}
        )
        self.hub.publish(success_event)
        self.assertEqual(self.ledger.progress.stagnation_count, 0)
        self.assertEqual(
            self.ledger.progress.iterations[-1].status, IterationStatus.PROGRESS
        )

    def test_multiple_subscribers(self):
        """
        Scenario: Multiple agents listening to the same channel.
        """
        counts = {"A": 0, "B": 0}

        def sub_a(event):
            counts["A"] += 1

        def sub_b(event):
            counts["B"] += 1

        self.hub.subscribe(EventType.HEARTBEAT, sub_a)
        self.hub.subscribe(EventType.HEARTBEAT, sub_b)

        self.hub.publish(Event(type=EventType.HEARTBEAT, source="sys"))

        self.assertEqual(counts["A"], 1)
        self.assertEqual(counts["B"], 1)


if __name__ == "__main__":
    unittest.main()
