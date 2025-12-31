"""
Tests for council/observability/middleware.py
"""

import pytest

from council.observability.middleware import (
    observable,
    Span,
    TraceCollector,
    LocalMemory,
    generate_trace_id,
    generate_span_id,
)


class TestLocalMemory:
    """Tests for LocalMemory"""

    def test_create_memory(self):
        """Test creating a local memory"""
        memory = LocalMemory(max_items=5)
        assert memory.max_items == 5
        assert len(memory._items) == 0

    def test_add_items_bounded(self):
        """Test that items are bounded by max_items"""
        memory = LocalMemory(max_items=3)
        for i in range(5):
            memory.add({"value": i})
        assert len(memory._items) == 3
        assert memory._items[0]["value"] == 2

    def test_get_recent(self):
        """Test getting recent items"""
        memory = LocalMemory()
        for i in range(5):
            memory.add({"value": i})
        recent = memory.get_recent(2)
        assert len(recent) == 2
        assert recent[0]["value"] == 3
        assert recent[1]["value"] == 4

    def test_search(self):
        """Test searching items"""
        memory = LocalMemory()
        memory.add({"type": "fact", "value": "A"})
        memory.add({"type": "decision", "value": "B"})
        memory.add({"type": "fact", "value": "C"})

        facts = memory.search("type", "fact")
        assert len(facts) == 2

    def test_to_context(self):
        """Test converting to context string"""
        memory = LocalMemory()
        memory.add({"key": "value"})
        context = memory.to_context()
        assert "Recent Memory" in context

    def test_clear(self):
        """Test clearing memory"""
        memory = LocalMemory()
        memory.add({"a": 1})
        memory.clear()
        assert len(memory._items) == 0


class TestSpan:
    """Tests for Span"""

    def test_create_span(self):
        """Test creating a span"""
        from datetime import datetime

        span = Span(
            trace_id="abc123",
            span_id="span1",
            parent_span_id=None,
            operation_name="test_op",
            agent_name="TestAgent",
            start_time=datetime.now(),
        )
        assert span.trace_id == "abc123"
        assert span.status == "OK"

    def test_add_event(self):
        """Test adding events to span"""
        from datetime import datetime

        span = Span(
            trace_id="abc",
            span_id="s1",
            parent_span_id=None,
            operation_name="test",
            agent_name="Agent",
            start_time=datetime.now(),
        )
        span.add_event("started", {"foo": "bar"})
        assert len(span.events) == 1
        assert span.events[0]["name"] == "started"

    def test_finish(self):
        """Test finishing a span"""
        from datetime import datetime

        span = Span(
            trace_id="abc",
            span_id="s1",
            parent_span_id=None,
            operation_name="test",
            agent_name="Agent",
            start_time=datetime.now(),
        )
        span.finish("ERROR")
        assert span.status == "ERROR"
        assert span.end_time is not None

    def test_to_dict(self):
        """Test converting span to dict"""
        from datetime import datetime

        span = Span(
            trace_id="abc",
            span_id="s1",
            parent_span_id=None,
            operation_name="test",
            agent_name="Agent",
            start_time=datetime.now(),
        )
        span.finish()
        d = span.to_dict()
        assert d["traceId"] == "abc"
        assert d["attributes"]["agent.name"] == "Agent"


class TestTraceCollector:
    """Tests for TraceCollector singleton"""

    def test_singleton(self):
        """Test that TraceCollector is a singleton"""
        c1 = TraceCollector()
        c2 = TraceCollector()
        assert c1 is c2

    def test_record_and_get(self):
        """Test recording and retrieving spans"""
        from datetime import datetime

        TraceCollector.clear()
        span = Span(
            trace_id="test",
            span_id="s1",
            parent_span_id=None,
            operation_name="op",
            agent_name="Agent",
            start_time=datetime.now(),
        )
        span.finish()
        TraceCollector.record(span)

        traces = TraceCollector.get_traces(limit=10)
        assert len(traces) >= 1


class TestObservableDecorator:
    """Tests for @observable decorator"""

    def test_observable_traces_method(self):
        """Test that observable decorator creates traces"""
        TraceCollector.clear()

        class MockAgent:
            name = "TestAgent"

            @observable
            def think(self, task):
                return f"Thinking about {task}"

        agent = MockAgent()
        result = agent.think("test task")

        assert result == "Thinking about test task"
        traces = TraceCollector.get_traces()
        assert len(traces) >= 1

    def test_observable_captures_errors(self):
        """Test that observable captures errors"""
        TraceCollector.clear()

        class MockAgent:
            name = "ErrorAgent"

            @observable
            def fail(self):
                raise ValueError("Test error")

        agent = MockAgent()
        with pytest.raises(ValueError):
            agent.fail()

        traces = TraceCollector.get_traces()
        # Should have recorded the span with ERROR status
        assert any(t["status"] == "ERROR" for t in traces)


class TestGenerators:
    """Tests for ID generators"""

    def test_generate_trace_id(self):
        """Test trace ID generation"""
        id1 = generate_trace_id()
        id2 = generate_trace_id()
        assert len(id1) == 16
        assert id1 != id2

    def test_generate_span_id(self):
        """Test span ID generation"""
        id1 = generate_span_id()
        id2 = generate_span_id()
        assert len(id1) == 8
        assert id1 != id2
