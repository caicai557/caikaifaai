"""
Tests for Hub and Event System (unittest version)
"""

import unittest
from council.orchestration.hub import Hub
from council.orchestration.events import Event, EventType
from council.orchestration.ledger import DualLedger


class TestHub(unittest.TestCase):
    def setUp(self):
        self.ledger = DualLedger.create(task_id="TEST-001", goal="Test Goal")
        self.hub = Hub(ledger=self.ledger)

    def test_pub_sub_basic(self):
        """测试基本的发布订阅功能"""
        received_events = []

        def callback(event: Event):
            received_events.append(event)

        self.hub.subscribe(EventType.TASK_CREATED, callback)

        event = Event(
            type=EventType.TASK_CREATED, source="test_agent", payload={"msg": "hello"}
        )
        self.hub.publish(event)

        self.assertEqual(len(received_events), 1)
        self.assertEqual(received_events[0].payload["msg"], "hello")
        self.assertEqual(received_events[0].source, "test_agent")

    def test_event_filtering(self):
        """测试事件过滤 (只接收订阅的类型)"""
        received_events = []

        def callback(event: Event):
            received_events.append(event)

        self.hub.subscribe(EventType.TASK_CREATED, callback)

        # 发布一个未订阅的事件类型
        event = Event(
            type=EventType.ERROR, source="test_agent", payload={"error": "oops"}
        )
        self.hub.publish(event)

        self.assertEqual(len(received_events), 0)

    def test_ledger_integration_fact(self):
        """测试通过事件自动更新 Ledger (Fact)"""
        event = Event(
            type=EventType.FACT_DISCOVERED,
            source="research_agent",
            payload={"key": "language", "value": "python"},
        )
        self.hub.publish(event)

        self.assertIn("language", self.ledger.task.known_facts)
        self.assertEqual(self.ledger.task.known_facts["language"], "python")

    def test_ledger_integration_query(self):
        """测试通过事件自动更新 Ledger (Query)"""
        # 1. Raise Query
        event1 = Event(
            type=EventType.QUERY_RAISED,
            source="planner",
            payload={"query": "what is the time?"},
        )
        self.hub.publish(event1)
        self.assertIn("what is the time?", self.ledger.task.pending_queries)

        # 2. Resolve Query
        event2 = Event(
            type=EventType.QUERY_RESOLVED,
            source="search_agent",
            payload={"query": "what is the time?", "result": "12:00"},
        )
        self.hub.publish(event2)
        self.assertNotIn("what is the time?", self.ledger.task.pending_queries)
        self.assertIn("resolved:what is the time?", self.ledger.task.known_facts)

    def test_ledger_integration_progress(self):
        """测试通过事件自动更新 Ledger (Progress)"""
        event = Event(
            type=EventType.CODE_WRITTEN, source="coder", payload={"file": "main.py"}
        )
        self.hub.publish(event)

        self.assertEqual(len(self.ledger.progress.iterations), 1)
        self.assertEqual(
            self.ledger.progress.iterations[0].action, "Event: artifact.code_written"
        )
        self.assertIn("main.py", self.ledger.progress.iterations[0].result)


if __name__ == "__main__":
    unittest.main()
