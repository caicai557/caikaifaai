"""
Observability Middleware - Distributed tracing for agents

Provides automatic tracing of agent actions with OpenTelemetry-compatible output.
"""

import functools
import logging
from typing import Any, Callable, Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)


class TraceLevel(Enum):
    """Trace verbosity levels"""

    MINIMAL = 1  # Only errors
    NORMAL = 2  # Errors + key actions
    VERBOSE = 3  # All actions


@dataclass
class Span:
    """
    A single span in a trace

    Represents one unit of work (e.g., one think() or vote() call).
    """

    trace_id: str
    span_id: str
    parent_span_id: Optional[str]
    operation_name: str
    agent_name: str
    start_time: datetime
    end_time: Optional[datetime] = None
    status: str = "OK"
    attributes: Dict[str, Any] = field(default_factory=dict)
    events: List[Dict[str, Any]] = field(default_factory=list)

    def add_event(self, name: str, attributes: Optional[Dict] = None) -> None:
        """Add an event to this span"""
        self.events.append(
            {
                "name": name,
                "timestamp": datetime.now().isoformat(),
                "attributes": attributes or {},
            }
        )

    def finish(self, status: str = "OK") -> None:
        """Finish the span"""
        self.end_time = datetime.now()
        self.status = status

    @property
    def duration_ms(self) -> float:
        """Get duration in milliseconds"""
        if self.end_time:
            return (self.end_time - self.start_time).total_seconds() * 1000
        return 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to OpenTelemetry-compatible dict"""
        return {
            "traceId": self.trace_id,
            "spanId": self.span_id,
            "parentSpanId": self.parent_span_id,
            "operationName": self.operation_name,
            "startTime": self.start_time.isoformat(),
            "endTime": self.end_time.isoformat() if self.end_time else None,
            "duration": self.duration_ms,
            "status": self.status,
            "attributes": {
                "agent.name": self.agent_name,
                **self.attributes,
            },
            "events": self.events,
        }


class TraceCollector:
    """
    Collects and stores traces

    Singleton pattern for global trace collection.
    """

    _instance: Optional["TraceCollector"] = None
    _spans: List[Span] = []
    _level: TraceLevel = TraceLevel.NORMAL

    def __new__(cls) -> "TraceCollector":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._spans = []
            cls._level = TraceLevel.NORMAL
        return cls._instance

    @classmethod
    def set_level(cls, level: TraceLevel) -> None:
        """Set trace verbosity level"""
        cls._level = level

    @classmethod
    def record(cls, span: Span) -> None:
        """Record a completed span"""
        cls._spans.append(span)
        # Keep only last 1000 spans
        if len(cls._spans) > 1000:
            cls._spans = cls._spans[-1000:]

    @classmethod
    def get_traces(cls, limit: int = 100) -> List[Dict]:
        """Get recent traces as dicts"""
        return [s.to_dict() for s in cls._spans[-limit:]]

    @classmethod
    def get_traces_for_agent(cls, agent_name: str, limit: int = 50) -> List[Dict]:
        """Get traces for a specific agent"""
        agent_spans = [s for s in cls._spans if s.agent_name == agent_name]
        return [s.to_dict() for s in agent_spans[-limit:]]

    @classmethod
    def clear(cls) -> None:
        """Clear all traces"""
        cls._spans = []


def generate_trace_id() -> str:
    """Generate a unique trace ID"""
    import uuid

    return uuid.uuid4().hex[:16]


def generate_span_id() -> str:
    """Generate a unique span ID"""
    import uuid

    return uuid.uuid4().hex[:8]


def observable(method: Callable) -> Callable:
    """
    Decorator to automatically trace agent methods

    Usage:
        class MyAgent(BaseAgent):
            @observable
            def think(self, task, context=None):
                ...
    """

    @functools.wraps(method)
    def wrapper(self, *args, **kwargs):
        agent_name = getattr(self, "name", "unknown")
        operation = f"{self.__class__.__name__}.{method.__name__}"

        span = Span(
            trace_id=generate_trace_id(),
            span_id=generate_span_id(),
            parent_span_id=None,
            operation_name=operation,
            agent_name=agent_name,
            start_time=datetime.now(),
            attributes={
                "args_count": len(args),
                "has_kwargs": bool(kwargs),
            },
        )

        try:
            result = method(self, *args, **kwargs)
            span.finish("OK")
            span.add_event("completed", {"result_type": type(result).__name__})
            return result
        except Exception as e:
            span.finish("ERROR")
            span.add_event("error", {"exception": str(e)})
            logger.error(f"[{operation}] Error: {e}")
            raise
        finally:
            TraceCollector.record(span)

    return wrapper


class LocalMemory:
    """
    Agent-scoped local memory

    Provides a bounded context window to prevent token overflow.
    Based on 2025 best practice: "Prioritize local memory for agents."
    """

    def __init__(self, max_items: int = 10):
        self.max_items = max_items
        self._items: List[Dict[str, Any]] = []

    def add(self, item: Dict[str, Any]) -> None:
        """Add an item to memory"""
        item["_timestamp"] = datetime.now().isoformat()
        self._items.append(item)
        if len(self._items) > self.max_items:
            self._items = self._items[-self.max_items :]

    def get_recent(self, n: int = 5) -> List[Dict[str, Any]]:
        """Get the N most recent items"""
        return self._items[-n:]

    def search(self, key: str, value: Any) -> List[Dict[str, Any]]:
        """Search for items matching a key-value pair"""
        return [item for item in self._items if item.get(key) == value]

    def clear(self) -> None:
        """Clear all memory"""
        self._items = []

    def to_context(self) -> str:
        """Convert to a context string for LLM prompts"""
        if not self._items:
            return "No recent memory."

        lines = ["## Recent Memory:"]
        for item in self._items[-5:]:
            lines.append(f"- {item}")
        return "\n".join(lines)


# Export
__all__ = [
    "observable",
    "Span",
    "TraceCollector",
    "TraceLevel",
    "LocalMemory",
    "generate_trace_id",
    "generate_span_id",
]
