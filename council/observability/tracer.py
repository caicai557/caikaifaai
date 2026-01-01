"""
Agent Tracer - OpenTelemetry 追踪 + 结构化日志 (2026 Enhanced)

基于 OpenTelemetry 2025 最佳实践:
- AI-specific semantic conventions
- BatchSpanProcessor
- Token/latency metrics

2026 Enhancements:
- Structured JSON logging
- Decision chain tracking
- Token usage analytics
- Cost estimation
"""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
from contextlib import contextmanager
from datetime import datetime
from enum import Enum
import json
import time
import threading
import logging

logger = logging.getLogger(__name__)

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


# ============== 2026 Structured Logging Enhancements ==============


class LogLevel(Enum):
    """Log levels for structured logging."""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class StructuredLogEntry:
    """
    Structured log entry for JSON logging (2026).

    Attributes:
        timestamp: ISO format timestamp
        level: Log level
        event_type: Type of event (llm_call, decision, tool_use, etc.)
        agent: Agent name
        model: Model used (if applicable)
        message: Human-readable message
        data: Additional structured data
        trace_id: Optional trace ID for correlation
        span_id: Optional span ID
    """
    timestamp: str
    level: str
    event_type: str
    agent: str
    message: str
    data: Dict[str, Any] = field(default_factory=dict)
    model: Optional[str] = None
    trace_id: Optional[str] = None
    span_id: Optional[str] = None

    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.__dict__, ensure_ascii=False, default=str)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {k: v for k, v in self.__dict__.items() if v is not None}


@dataclass
class DecisionRecord:
    """
    Record of an agent decision (2026).

    Used for decision chain tracking and audit.
    """
    timestamp: str
    agent: str
    decision: str
    rationale: str
    confidence: float
    alternatives: List[str] = field(default_factory=list)
    context: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return self.__dict__


@dataclass
class TokenUsageRecord:
    """
    Token usage record for cost tracking (2026).
    """
    timestamp: str
    model: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    estimated_cost_usd: float
    task_type: str = ""
    agent: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return self.__dict__


# Model pricing (USD per 1K tokens) - 2026 estimates
MODEL_PRICING = {
    "claude-sonnet-4-20250514": {"input": 0.003, "output": 0.015},
    "claude-3-5-sonnet-20241022": {"input": 0.003, "output": 0.015},
    "claude-3-opus-20240229": {"input": 0.015, "output": 0.075},
    "gpt-4o": {"input": 0.005, "output": 0.015},
    "gpt-4o-mini": {"input": 0.00015, "output": 0.0006},
    "gemini-2.0-flash": {"input": 0.00025, "output": 0.001},
    "gemini-1.5-pro": {"input": 0.00125, "output": 0.005},
    "deepseek-chat": {"input": 0.00014, "output": 0.00028},
    "default": {"input": 0.001, "output": 0.002},
}


def estimate_cost(model: str, prompt_tokens: int, completion_tokens: int) -> float:
    """Estimate cost in USD for token usage."""
    pricing = MODEL_PRICING.get(model, MODEL_PRICING["default"])
    input_cost = (prompt_tokens / 1000) * pricing["input"]
    output_cost = (completion_tokens / 1000) * pricing["output"]
    return round(input_cost + output_cost, 6)


class StructuredLogger:
    """
    Structured JSON logger for Council framework (2026).

    Provides:
    - JSON formatted log output
    - Decision chain tracking
    - Token usage analytics
    - Cost estimation

    Example:
        slogger = StructuredLogger("council-agent")
        slogger.log_decision(
            agent="planner",
            decision="Use parallel execution",
            rationale="Multiple independent subtasks detected",
            confidence=0.85
        )
    """

    def __init__(
        self,
        service_name: str = "council",
        output_json: bool = True,
        track_decisions: bool = True,
        track_tokens: bool = True,
    ):
        self.service_name = service_name
        self.output_json = output_json
        self.track_decisions = track_decisions
        self.track_tokens = track_tokens

        self._lock = threading.Lock()
        self._decision_chain: List[DecisionRecord] = []
        self._token_usage: List[TokenUsageRecord] = []
        self._total_cost_usd: float = 0.0

    def _emit(self, entry: StructuredLogEntry) -> None:
        """Emit a log entry."""
        if self.output_json:
            print(entry.to_json())
        else:
            logger.log(
                getattr(logging, entry.level.upper(), logging.INFO),
                f"[{entry.event_type}] {entry.agent}: {entry.message}",
                extra=entry.data
            )

    def log(
        self,
        level: str,
        event_type: str,
        agent: str,
        message: str,
        model: Optional[str] = None,
        **data,
    ) -> StructuredLogEntry:
        """Create and emit a structured log entry."""
        entry = StructuredLogEntry(
            timestamp=datetime.now().isoformat(),
            level=level,
            event_type=event_type,
            agent=agent,
            message=message,
            model=model,
            data=data,
        )
        self._emit(entry)
        return entry

    def log_decision(
        self,
        agent: str,
        decision: str,
        rationale: str,
        confidence: float = 0.0,
        alternatives: Optional[List[str]] = None,
        **context,
    ) -> DecisionRecord:
        """
        Log a decision with rationale (2026).

        Args:
            agent: Agent making the decision
            decision: The decision made
            rationale: Why this decision was made
            confidence: Confidence level (0-1)
            alternatives: Other options considered
            context: Additional context

        Returns:
            DecisionRecord
        """
        record = DecisionRecord(
            timestamp=datetime.now().isoformat(),
            agent=agent,
            decision=decision,
            rationale=rationale,
            confidence=confidence,
            alternatives=alternatives or [],
            context=context,
        )

        if self.track_decisions:
            with self._lock:
                self._decision_chain.append(record)

        self.log(
            level="info",
            event_type="decision",
            agent=agent,
            message=f"Decision: {decision}",
            rationale=rationale,
            confidence=confidence,
        )

        return record

    def log_token_usage(
        self,
        model: str,
        prompt_tokens: int,
        completion_tokens: int,
        task_type: str = "",
        agent: str = "",
    ) -> TokenUsageRecord:
        """
        Log token usage with cost estimation (2026).

        Args:
            model: Model name
            prompt_tokens: Input tokens
            completion_tokens: Output tokens
            task_type: Type of task
            agent: Agent name

        Returns:
            TokenUsageRecord
        """
        total_tokens = prompt_tokens + completion_tokens
        cost = estimate_cost(model, prompt_tokens, completion_tokens)

        record = TokenUsageRecord(
            timestamp=datetime.now().isoformat(),
            model=model,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
            estimated_cost_usd=cost,
            task_type=task_type,
            agent=agent,
        )

        if self.track_tokens:
            with self._lock:
                self._token_usage.append(record)
                self._total_cost_usd += cost

        self.log(
            level="info",
            event_type="token_usage",
            agent=agent or "system",
            message=f"Tokens: {total_tokens} (${cost:.4f})",
            model=model,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            cost_usd=cost,
        )

        return record

    def log_error(
        self,
        agent: str,
        error: str,
        error_type: str = "unknown",
        **context,
    ) -> StructuredLogEntry:
        """Log an error."""
        return self.log(
            level="error",
            event_type="error",
            agent=agent,
            message=error,
            error_type=error_type,
            **context,
        )

    def log_llm_call(
        self,
        agent: str,
        model: str,
        prompt_preview: str,
        response_preview: str = "",
        latency_ms: float = 0,
        success: bool = True,
        **extra,
    ) -> StructuredLogEntry:
        """Log an LLM API call."""
        return self.log(
            level="info" if success else "error",
            event_type="llm_call",
            agent=agent,
            message=f"LLM call to {model}" + (" OK" if success else " FAILED"),
            model=model,
            prompt_preview=prompt_preview[:200],
            response_preview=response_preview[:200] if response_preview else "",
            latency_ms=latency_ms,
            success=success,
            **extra,
        )

    def get_decision_chain(self) -> List[DecisionRecord]:
        """Get the full decision chain."""
        with self._lock:
            return list(self._decision_chain)

    def get_token_usage(self) -> List[TokenUsageRecord]:
        """Get all token usage records."""
        with self._lock:
            return list(self._token_usage)

    def get_total_cost(self) -> float:
        """Get total estimated cost in USD."""
        with self._lock:
            return self._total_cost_usd

    def get_usage_summary(self) -> Dict[str, Any]:
        """Get token usage summary by model."""
        with self._lock:
            summary: Dict[str, Dict[str, Any]] = {}
            for record in self._token_usage:
                if record.model not in summary:
                    summary[record.model] = {
                        "calls": 0,
                        "prompt_tokens": 0,
                        "completion_tokens": 0,
                        "total_tokens": 0,
                        "cost_usd": 0.0,
                    }
                s = summary[record.model]
                s["calls"] += 1
                s["prompt_tokens"] += record.prompt_tokens
                s["completion_tokens"] += record.completion_tokens
                s["total_tokens"] += record.total_tokens
                s["cost_usd"] += record.estimated_cost_usd

            return {
                "by_model": summary,
                "total_cost_usd": self._total_cost_usd,
                "total_calls": len(self._token_usage),
            }

    def export_decision_chain(self, format: str = "json") -> str:
        """
        Export decision chain (2026).

        Args:
            format: "json" or "mermaid"

        Returns:
            Exported string
        """
        chain = self.get_decision_chain()

        if format == "json":
            return json.dumps([r.to_dict() for r in chain], indent=2, ensure_ascii=False)

        elif format == "mermaid":
            lines = ["graph TD"]
            for i, record in enumerate(chain):
                node_id = f"D{i}"
                label = f"{record.agent}: {record.decision[:30]}"
                lines.append(f"    {node_id}[\"{label}\"]")
                if i > 0:
                    lines.append(f"    D{i-1} --> {node_id}")
            return "\n".join(lines)

        return ""

    def clear(self) -> None:
        """Clear all tracked data."""
        with self._lock:
            self._decision_chain.clear()
            self._token_usage.clear()
            self._total_cost_usd = 0.0


# Default structured logger instance
default_slogger = StructuredLogger()


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
    # Core Tracer
    "AgentTracer",
    "LLMAttributes",
    "AgentAttributes",
    # 2026 Structured Logging
    "StructuredLogger",
    "StructuredLogEntry",
    "DecisionRecord",
    "TokenUsageRecord",
    "LogLevel",
    "default_slogger",
    "estimate_cost",
    "MODEL_PRICING",
]
