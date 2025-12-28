"""
Boundary Tests for Hub and Event System
Focus: Edge cases, High Load, Invalid Inputs
"""

import unittest
import time
from council.orchestration.hub import Hub
from council.orchestration.events import Event, EventType
from council.orchestration.ledger import DualLedger


class TestHubBoundary(unittest.TestCase):
    def setUp(self):
        self.ledger = DualLedger.create(task_id="TEST-BOUNDARY", goal="Stress Test")
        self.hub = Hub(ledger=self.ledger)

    def test_high_volume_events(self):
        """
        Boundary: Publish 10,000 events in rapid succession.
        Verify: No crash, all events processed (synchronously).
        """
        count = 0

        def counter(event):
            nonlocal count
            count += 1

        self.hub.subscribe(EventType.HEARTBEAT, counter)

        start_time = time.time()
        for _ in range(10000):
            self.hub.publish(Event(type=EventType.HEARTBEAT, source="load_test"))
        end_time = time.time()

        self.assertEqual(count, 10000)
        print(f"\n[Perf] Processed 10,000 events in {end_time - start_time:.4f}s")

    def test_recursive_publish(self):
        """
        Boundary: Subscriber publishes an event (Recursion Depth).
        Verify: Hub handles nested publishing without infinite loop.
        """
        depth = 0
        max_depth = 10

        def recursive_publisher(event):
            nonlocal depth
            if depth < max_depth:
                depth += 1
                self.hub.publish(Event(type=EventType.HEARTBEAT, source="recursive"))

        self.hub.subscribe(EventType.HEARTBEAT, recursive_publisher)

        # Trigger
        self.hub.publish(Event(type=EventType.HEARTBEAT, source="root"))

        # Initial + 10 recursive calls = 11 total events processed by this subscriber
        # But wait, the subscriber is called for EACH event.
        # 1st event -> depth=1, pub(2nd)
        # 2nd event -> depth=2, pub(3rd)
        # ...
        # 10th event -> depth=10, pub(11th)
        # 11th event -> depth=10 (no inc), stop.
        self.assertEqual(depth, 10)

    def test_invalid_event_creation(self):
        """
        Boundary: Creating events with invalid types via factory.
        """
        # 1. Unknown type string -> defaults to FACT_DISCOVERED
        event = Event.create("UNKNOWN_TYPE_XYZ", "tester")
        self.assertEqual(event.type, EventType.FACT_DISCOVERED)
        self.assertEqual(event.payload["original_type"], "UNKNOWN_TYPE_XYZ")

        # 2. Empty source
        event2 = Event.create("task.created", "")
        self.assertEqual(event2.source, "")

    def test_ledger_overflow_protection(self):
        """
        Boundary: Ledger stagnation count shouldn't overflow or behave oddly.
        """
        # Manually set high stagnation
        self.ledger.progress.stagnation_count = 999999

        # Fail again
        self.hub.publish(Event(type=EventType.TEST_FAILED, source="qa"))
        self.assertEqual(self.ledger.progress.stagnation_count, 1000000)

        # Success resets it
        self.hub.publish(Event(type=EventType.TEST_PASSED, source="qa"))
        self.assertEqual(self.ledger.progress.stagnation_count, 0)

    def test_subscriber_exception_isolation(self):
        """
        Boundary: Multiple subscribers, one raises Exception.
        Verify: Others still run.
        """
        log = []

        def bad_sub(e):
            raise RuntimeError("Boom")

        def good_sub(e):
            log.append("ok")

        self.hub.subscribe(EventType.HEARTBEAT, bad_sub)
        self.hub.subscribe(EventType.HEARTBEAT, good_sub)

        self.hub.publish(Event(type=EventType.HEARTBEAT, source="test"))

        self.assertEqual(log, ["ok"])


if __name__ == "__main__":
    unittest.main()
