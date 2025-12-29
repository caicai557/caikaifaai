# Tests for Streaming Enhancements
import pytest


class TestStreamWithThinking:
    @pytest.mark.asyncio
    async def test_stream_with_thinking_basic(self):
        from council.streaming.async_stream import StreamingLLM
        streamer = StreamingLLM()
        thinking_states = []
        content_chunks = []
        result = await streamer.stream_with_thinking(
            prompt="Test prompt",
            model="mock",
            on_thinking=lambda s: thinking_states.append(s),
            on_content=lambda c: content_chunks.append(c),
        )
        assert result is not None
        assert "text" in result
        assert "metrics" in result
        assert "ttft_ms" in result["metrics"]

    @pytest.mark.asyncio
    async def test_ttft_metric(self):
        from council.streaming.async_stream import StreamingLLM
        streamer = StreamingLLM()
        result = await streamer.stream_with_thinking(prompt="Test", model="mock")
        assert result["metrics"]["ttft_ms"] >= 0


class TestSSEStreaming:
    @pytest.mark.asyncio
    async def test_stream_as_sse(self):
        from council.streaming.async_stream import StreamingLLM
        streamer = StreamingLLM()
        events = []
        async for event in streamer.stream_as_sse("Test", "mock"):
            events.append(event)
        assert any("event: start" in e for e in events)
        assert any("event: done" in e for e in events)

    @pytest.mark.asyncio
    async def test_sse_format_valid(self):
        from council.streaming.async_stream import StreamingLLM
        streamer = StreamingLLM()
        async for event in streamer.stream_as_sse("Test", "mock"):
            assert event.endswith("\n\n")


class TestSSEFormatter:
    def test_format_event(self):
        from council.streaming.async_stream import SSEFormatter
        result = SSEFormatter.format_event("test", {"key": "value"})
        assert "event: test" in result
        assert result.endswith("\n\n")

    def test_format_chunk(self):
        from council.streaming.async_stream import SSEFormatter
        result = SSEFormatter.format_chunk("Hello world")
        assert result == "data: Hello world\n\n"

    def test_format_done(self):
        from council.streaming.async_stream import SSEFormatter
        result = SSEFormatter.format_done()
        assert "event: done" in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
