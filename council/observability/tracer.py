"""
Agent Tracer - OpenTelemetry 追踪

基于 OpenTelemetry 2025 最佳实践:
- AI-specific semantic conventions
- BatchSpanProcessor
- Token/latency metrics
"""

from dataclasses import dataclass
from typing import Dict, Any
from contextlib import contextmanager
import time
import threading

# 尝试导入 OpenTelemetry，如果不可用则使用 Mock
try:
    from opentelemetry import trace
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import SimpleSpanProcessor, ConsoleSpanExporter
    from opentelemetry.sdk.resources import Resource

    HAS_OTEL = True
except ImportError:
    HAS_OTEL = False
    trace = None


@dataclass
class LLMAttributes:
    """LLM 调用语义属性"""

    model: str
    prompt_tokens: int = 0
    completion_tokens: int = 0
    temperature: float = 0.7

    def to_dict(self) -> Dict[str, Any]:
        return {
            "gen_ai.system": self.model,
            "gen_ai.token_count.prompt": self.prompt_tokens,
            "gen_ai.token_count.completion": self.completion_tokens,
            "gen_ai.temperature": self.temperature,
        }


@dataclass
class AgentAttributes:
    """Agent 执行属性"""

    agent_name: str
    task: str = ""
    confidence: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "agent.name": self.agent_name,
            "agent.task": self.task,
            "agent.confidence": self.confidence,
        }


class AgentTracer:
    """
    Agent 追踪器

    提供 OpenTelemetry 集成用于:
    - 追踪 LLM 调用
    - 追踪工具使用
    - 追踪 Agent 步骤
    - 记录 Token 和延迟指标
    """

    def __init__(self, service_name: str = "council-agent"):
        self.service_name = service_name
        self._lock = threading.Lock()
        self._stats = {
            "total_prompt_tokens": 0,
            "total_completion_tokens": 0,
            "latencies": [],
        }

        if HAS_OTEL:
            resource = Resource.create({"service.name": service_name})
            provider = TracerProvider(resource=resource)
            provider.add_span_processor(SimpleSpanProcessor(ConsoleSpanExporter()))
            trace.set_tracer_provider(provider)
            self.tracer = trace.get_tracer(__name__)
        else:
            self.tracer = MockTracer()

    @contextmanager
    def trace_llm_call(
        self,
        model: str,
        prompt: str,
        **kwargs,
    ):
        """追踪 LLM 调用"""
        start_time = time.time()

        try:
            if HAS_OTEL:
                with self.tracer.start_as_current_span("llm_call") as span:
                    span.set_attribute("gen_ai.system", model)
                    span.set_attribute("gen_ai.prompt", prompt[:500])  # 截断
                    for k, v in kwargs.items():
                        span.set_attribute(f"gen_ai.{k}", v)
                    yield span
            else:
                span = MockSpan()
                span.set_attribute("gen_ai.system", model)
                span.set_attribute("gen_ai.prompt", prompt[:500])
                yield span
        finally:
            # 记录延迟 (即使发生异常)
            latency_ms = (time.time() - start_time) * 1000
            with self._lock:
                self._stats["latencies"].append(latency_ms)

    @contextmanager
    def trace_tool_call(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
    ):
        """追踪工具调用"""
        if HAS_OTEL:
            with self.tracer.start_as_current_span("tool_call") as span:
                span.set_attribute("tool.name", tool_name)
                span.set_attribute("tool.arguments", str(arguments)[:200])
                yield span
        else:
            span = MockSpan()
            span.set_attribute("tool.name", tool_name)
            yield span

    @contextmanager
    def trace_agent_step(
        self,
        agent_name: str,
        step_type: str,
    ):
        """追踪 Agent 步骤"""
        if HAS_OTEL:
            with self.tracer.start_as_current_span(f"agent_{step_type}") as span:
                span.set_attribute("agent.name", agent_name)
                span.set_attribute("agent.step_type", step_type)
                yield span
        else:
            span = MockSpan()
            span.set_attribute("agent.name", agent_name)
            span.set_attribute("agent.step_type", step_type)
            yield span

    def record_tokens(
        self,
        model: str,
        prompt: int,
        completion: int,
    ) -> None:
        """记录 Token 使用量"""
        with self._lock:
            self._stats["total_prompt_tokens"] += prompt
            self._stats["total_completion_tokens"] += completion

    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        with self._lock:
            stats = dict(self._stats)
            if stats["latencies"]:
                stats["avg_latency_ms"] = sum(stats["latencies"]) / len(
                    stats["latencies"]
                )
            else:
                stats["avg_latency_ms"] = 0
            return stats


class MockTracer:
    """Mock tracer for when OpenTelemetry is not available"""

    def start_as_current_span(self, name: str):
        return MockSpanContext(name)


class MockSpanContext:
    """Mock span context manager"""

    def __init__(self, name: str):
        self.name = name

    def __enter__(self):
        return MockSpan()

    def __exit__(self, *args):
        pass


class MockSpan:
    """Mock span for testing without OpenTelemetry"""

    def __init__(self):
        self._attributes = {}

    def set_attribute(self, key: str, value: Any) -> None:
        self._attributes[key] = value

    def get_attribute(self, key: str) -> Any:
        return self._attributes.get(key)


__all__ = [
    "AgentTracer",
    "LLMAttributes",
    "AgentAttributes",
]
