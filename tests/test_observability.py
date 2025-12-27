"""
TDD Tests for Observability Module
"""

import unittest
from council.orchestration.hub import Hub
from council.orchestration.events import Event, EventType
from council.orchestration.ledger import DualLedger


class TestObservability(unittest.TestCase):
    """Tests for Observability module."""

    def setUp(self):
        self.ledger = DualLedger.create(task_id="OBS-TEST", goal="Observability Test")
        self.hub = Hub(ledger=self.ledger)

    def test_tracer_creates_spans(self):
        """Tracer should create spans for operations."""
        from council.agents.observability import Tracer

        tracer = Tracer(service_name="test")
        span = tracer.start_span("test_operation")

        self.assertEqual(span.name, "test_operation")
        self.assertIsNotNone(span.trace_id)

        span.end()
        self.assertIsNotNone(span.end_time)

    def test_hub_observer_records_events(self):
        """HubObserver should record all Hub events."""
        from council.agents.observability import HubObserver, Tracer

        tracer = Tracer()
        _ = HubObserver(hub=self.hub, tracer=tracer)  # noqa: F841

        # Publish an event
        self.hub.publish(Event(type=EventType.HEARTBEAT, source="test"))

        # Observer should have recorded it
        spans = tracer.get_all_spans()
        self.assertGreater(len(spans), 0)

    def test_traced_decorator(self):
        """traced decorator should wrap functions with spans."""
        from council.agents.observability import Tracer, traced

        tracer = Tracer()

        @traced(tracer)
        def my_function():
            return "result"

        result = my_function()

        self.assertEqual(result, "result")
        spans = tracer.get_all_spans()
        self.assertGreater(len(spans), 0)
        self.assertEqual(spans[0]["name"], "my_function")


if __name__ == "__main__":
    unittest.main()
