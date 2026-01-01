"""
Observability Module - OpenTelemetry 集成 + 结构化日志 (2026 Enhanced)

提供:
- AgentTracer: Agent 追踪器
- LLMAttributes: LLM 语义属性
- AgentAttributes: Agent 属性
- StructuredLogger: 结构化 JSON 日志
- DecisionRecord: 决策记录
- TokenUsageRecord: Token 使用记录
- DecisionVisualizer: 决策可视化
"""

from council.observability.tracer import (
    AgentTracer,
    LLMAttributes,
    AgentAttributes,
    # 2026 Structured Logging
    StructuredLogger,
    StructuredLogEntry,
    DecisionRecord,
    TokenUsageRecord,
    LogLevel,
    default_slogger,
    estimate_cost,
    MODEL_PRICING,
)
from council.observability.decision_viz import (
    DecisionNode,
    DecisionVisualizer,
    visualize_from_records,
)

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
    # 2026 Decision Visualization
    "DecisionNode",
    "DecisionVisualizer",
    "visualize_from_records",
]
