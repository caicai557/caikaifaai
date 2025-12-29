"""
Tests for Streaming LLM Responses

TDD: 先写测试，后实现
"""

import pytest


# =============================================================
# Test: StreamingLLM
# =============================================================


class TestStreamingLLM:
    """StreamingLLM 测试"""

    @pytest.mark.asyncio
    async def test_stream_initialization(self):
        """测试流初始化"""
        from council.streaming.async_stream import StreamingLLM

        streamer = StreamingLLM()
        assert streamer is not None

    @pytest.mark.asyncio
    async def test_mock_stream(self):
        """测试模拟流"""
        from council.streaming.async_stream import StreamingLLM

        streamer = StreamingLLM()

        chunks = []
        async for chunk in streamer.mock_stream("Hello"):
            chunks.append(chunk)

        assert len(chunks) > 0
        assert "".join(chunks) != ""

    @pytest.mark.asyncio
    async def test_stream_aggregation(self):
        """测试流聚合"""
        from council.streaming.async_stream import StreamingLLM

        streamer = StreamingLLM()

        full_response = await streamer.stream_to_string(
            prompt="Test prompt",
            model="mock",
        )

        assert isinstance(full_response, str)
        assert len(full_response) > 0


# =============================================================
# Test: Stream Handlers
# =============================================================


class TestStreamHandlers:
    """流处理器测试"""

    @pytest.mark.asyncio
    async def test_chunk_callback(self):
        """测试 chunk 回调"""
        from council.streaming.async_stream import StreamingLLM

        chunks_received = []

        def on_chunk(chunk: str):
            chunks_received.append(chunk)

        streamer = StreamingLLM()
        await streamer.stream_with_callback(
            prompt="Test",
            model="mock",
            on_chunk=on_chunk,
        )

        assert len(chunks_received) > 0

    @pytest.mark.asyncio
    async def test_token_counter_stream(self):
        """测试流式 Token 计数"""
        from council.streaming.async_stream import StreamingLLM

        streamer = StreamingLLM()

        result = await streamer.stream_with_metrics(
            prompt="Test prompt",
            model="mock",
        )

        assert "text" in result
        assert "metrics" in result
        assert "tokens" in result["metrics"]


# =============================================================
# Test: Error Handling
# =============================================================


class TestStreamErrorHandling:
    """流错误处理测试"""

    @pytest.mark.asyncio
    async def test_stream_timeout(self):
        """测试流超时"""
        from council.streaming.async_stream import StreamingLLM, StreamTimeoutError

        streamer = StreamingLLM()

        with pytest.raises(StreamTimeoutError):
            async for _ in streamer.stream_with_timeout(
                prompt="Test",
                model="slow_mock",
                timeout=0.001,  # 极短超时
            ):
                pass

    @pytest.mark.asyncio
    async def test_stream_recovery(self):
        """测试流恢复"""
        from council.streaming.async_stream import StreamingLLM

        streamer = StreamingLLM()

        # 模拟中断后恢复
        partial = []
        try:
            async for chunk in streamer.stream_with_interruption(
                prompt="Test",
                model="mock",
                interrupt_at=3,
            ):
                partial.append(chunk)
        except Exception:
            pass

        # 应该有部分内容
        assert len(partial) > 0


# =============================================================
# Test: Multi-Model Streaming
# =============================================================


class TestMultiModelStreaming:
    """多模型流测试"""

    @pytest.mark.asyncio
    async def test_model_detection(self):
        """测试模型检测"""
        from council.streaming.async_stream import StreamingLLM

        streamer = StreamingLLM()

        assert streamer._detect_provider("claude-4.5-sonnet") == "anthropic"
        assert streamer._detect_provider("gemini-3-flash") == "google"
        assert streamer._detect_provider("gpt-5.2-codex") == "openai"

    @pytest.mark.asyncio
    async def test_unified_interface(self):
        """测试统一接口"""
        from council.streaming.async_stream import StreamingLLM

        streamer = StreamingLLM()

        # 所有模型使用相同接口
        for model in ["mock-claude", "mock-gemini", "mock-gpt"]:
            chunks = []
            async for chunk in streamer.stream(prompt="Test", model=model):
                chunks.append(chunk)
            assert len(chunks) > 0
