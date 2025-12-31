"""
Observability - 可观测性模块
提供结构化日志、追踪和指标收集。
"""

import logging
import json
from datetime import datetime
from typing import Dict, Any, Optional
from dataclasses import dataclass, field
from functools import wraps

from council.orchestration.hub import Hub
from council.orchestration.events import Event, EventType


# 配置 JSON 格式日志
class JSONFormatter(logging.Formatter):
    """JSON 格式日志"""

    def format(self, record):
        log_record = {
            "timestamp": datetime.now().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if hasattr(record, "event_data"):
            log_record["event"] = record.event_data
        if hasattr(record, "agent_name"):
            log_record["agent"] = record.agent_name
        if hasattr(record, "trace_id"):
            log_record["trace_id"] = record.trace_id
        return json.dumps(log_record, ensure_ascii=False)


@dataclass
class Span:
    """追踪 Span"""

    name: str
    trace_id: str
    start_time: datetime = field(default_factory=datetime.now)
    end_time: Optional[datetime] = None
    attributes: Dict[str, Any] = field(default_factory=dict)
    events: list = field(default_factory=list)

    def end(self):
        self.end_time = datetime.now()

    def add_event(self, name: str, attributes: Dict[str, Any] = None):
        self.events.append(
            {
                "name": name,
                "timestamp": datetime.now().isoformat(),
                "attributes": attributes or {},
            }
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "trace_id": self.trace_id,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "duration_ms": (
                (self.end_time - self.start_time).total_seconds() * 1000
                if self.end_time
                else None
            ),
            "attributes": self.attributes,
            "events": self.events,
        }


class Tracer:
    """简易追踪器"""

    MAX_SPANS = 10000  # 内存保护

    def __init__(self, service_name: str = "agent-council"):
        self.service_name = service_name
        self.spans: list = []
        self.logger = logging.getLogger("Tracer")

    def start_span(self, name: str, trace_id: str = None) -> Span:
        """开始一个新的 Span"""
        import uuid

        trace_id = trace_id or str(uuid.uuid4())
        span = Span(name=name, trace_id=trace_id)
        self.spans.append(span)

        # 内存保护: 限制 Span 数量
        if len(self.spans) > self.MAX_SPANS:
            self.spans = self.spans[-self.MAX_SPANS :]

        self.logger.debug(f"Started span: {name} (trace_id: {trace_id})")
        return span

    def get_all_spans(self) -> list:
        """获取所有 Span"""
        return [s.to_dict() for s in self.spans]


class HubObserver:
    """Hub 事件观察者"""

    def __init__(self, hub: Hub, tracer: Tracer = None):
        self.hub = hub
        self.tracer = tracer or Tracer()
        self.logger = logging.getLogger("HubObserver")
        self._subscribe_all()

    def _subscribe_all(self):
        """订阅所有事件类型"""
        for event_type in EventType:
            self.hub.subscribe(event_type, self._on_event)

    def _on_event(self, event: Event):
        """记录事件"""
        log_data = {
            "event_id": event.event_id,
            "type": event.type.value,
            "source": event.source,
            "timestamp": event.timestamp.isoformat(),
            "payload_keys": list(event.payload.keys()),
        }
        self.logger.info(
            f"Event observed: {event.type.value}",
            extra={"event_data": log_data},
        )

        # 创建追踪 Span
        span = self.tracer.start_span(
            name=f"event.{event.type.value}",
            trace_id=event.event_id,
        )
        span.attributes["source"] = event.source
        span.add_event("received", {"payload_size": len(str(event.payload))})
        span.end()


def traced(tracer: Tracer):
    """函数追踪装饰器"""

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            span = tracer.start_span(name=func.__name__)
            try:
                result = func(*args, **kwargs)
                span.add_event("completed", {"success": True})
                return result
            except Exception as e:
                span.add_event("error", {"exception": str(e)})
                raise
            finally:
                span.end()

        return wrapper

    return decorator


__all__ = [
    "JSONFormatter",
    "Span",
    "Tracer",
    "HubObserver",
    "traced",
]
