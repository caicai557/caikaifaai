"""
Tests for OpenTelemetry Tracing

TDD: 先写测试，后实现
"""


# =============================================================
# Test: AgentTracer
# =============================================================


class TestAgentTracer:
    """AgentTracer 测试"""

    def test_tracer_initialization(self):
        """测试 Tracer 初始化"""
        from council.observability.tracer import AgentTracer

        tracer = AgentTracer(service_name="test-service")
        assert tracer.service_name == "test-service"
        assert tracer.tracer is not None

    def test_trace_llm_call(self):
        """测试追踪 LLM 调用"""
        from council.observability.tracer import AgentTracer

        tracer = AgentTracer(service_name="test")

        with tracer.trace_llm_call(
            model="claude-4.5-sonnet",
            prompt="Hello, world!",
        ) as span:
            assert span is not None
            # 模拟 LLM 响应
            span.set_attribute("gen_ai.completion", "Hi there!")
            span.set_attribute("gen_ai.token_count.prompt", 3)
            span.set_attribute("gen_ai.token_count.completion", 2)

    def test_trace_tool_call(self):
        """测试追踪工具调用"""
        from council.observability.tracer import AgentTracer

        tracer = AgentTracer(service_name="test")

        with tracer.trace_tool_call(
            tool_name="search",
            arguments={"query": "test"},
        ) as span:
            assert span is not None
            span.set_attribute("tool.result", "found 5 results")

    def test_trace_agent_step(self):
        """测试追踪 Agent 步骤"""
        from council.observability.tracer import AgentTracer

        tracer = AgentTracer(service_name="test")

        with tracer.trace_agent_step(
            agent_name="Coder",
            step_type="execute",
        ) as span:
            assert span is not None


# =============================================================
# Test: Span Attributes
# =============================================================


class TestSpanAttributes:
    """Span 属性测试"""

    def test_llm_attributes(self):
        """测试 LLM 语义属性"""
        from council.observability.tracer import LLMAttributes

        attrs = LLMAttributes(
            model="gemini-3-pro",
            prompt_tokens=100,
            completion_tokens=50,
            temperature=0.7,
        )

        data = attrs.to_dict()
        assert data["gen_ai.system"] == "gemini-3-pro"
        assert data["gen_ai.token_count.prompt"] == 100
        assert data["gen_ai.token_count.completion"] == 50

    def test_agent_attributes(self):
        """测试 Agent 属性"""
        from council.observability.tracer import AgentAttributes

        attrs = AgentAttributes(
            agent_name="Orchestrator",
            task="Plan feature",
            confidence=0.85,
        )

        data = attrs.to_dict()
        assert data["agent.name"] == "Orchestrator"
        assert data["agent.confidence"] == 0.85


# =============================================================
# Test: Metrics
# =============================================================


class TestMetrics:
    """指标测试"""

    def test_token_counter(self):
        """测试 Token 计数器"""
        from council.observability.tracer import AgentTracer

        tracer = AgentTracer(service_name="test")

        tracer.record_tokens(model="claude-4.5", prompt=100, completion=50)
        tracer.record_tokens(model="claude-4.5", prompt=200, completion=100)

        stats = tracer.get_stats()
        assert stats["total_prompt_tokens"] == 300
        assert stats["total_completion_tokens"] == 150

    def test_latency_histogram(self):
        """测试延迟直方图"""
        from council.observability.tracer import AgentTracer
        import time

        tracer = AgentTracer(service_name="test")

        with tracer.trace_llm_call(model="test", prompt="test"):
            time.sleep(0.01)  # 模拟延迟

        # 延迟应该被记录
        stats = tracer.get_stats()
        assert "avg_latency_ms" in stats
