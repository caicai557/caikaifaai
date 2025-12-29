"""
Async Stream - 异步流式 LLM 调用

支持:
- Claude API 流式
- Gemini API 流式
- 统一接口
"""

from typing import AsyncGenerator, Callable, Dict, Any
import asyncio


class StreamTimeoutError(Exception):
    """流超时异常"""

    pass


class StreamingLLM:
    """
    流式 LLM 调用器

    提供统一接口支持多种 LLM 的流式输出
    """

    def __init__(self):
        self._providers = {
            "anthropic": self._stream_claude,
            "google": self._stream_gemini,
            "openai": self._stream_openai,
            "mock": self._stream_mock,
        }

    def _detect_provider(self, model: str) -> str:
        """检测模型提供商"""
        model_lower = model.lower()
        if "claude" in model_lower:
            return "anthropic"
        elif "gemini" in model_lower:
            return "google"
        elif "gpt" in model_lower or "codex" in model_lower:
            return "openai"
        else:
            return "mock"

    async def stream(
        self,
        prompt: str,
        model: str,
        **kwargs,
    ) -> AsyncGenerator[str, None]:
        """
        统一流式接口

        Args:
            prompt: 提示词
            model: 模型名称
            **kwargs: 额外参数

        Yields:
            文本块
        """
        provider = self._detect_provider(model)
        stream_fn = self._providers.get(provider, self._stream_mock)

        async for chunk in stream_fn(prompt, model, **kwargs):
            yield chunk

    async def mock_stream(self, prompt: str) -> AsyncGenerator[str, None]:
        """Mock 流 (用于测试)"""
        async for chunk in self._stream_mock(prompt, "mock"):
            yield chunk

    async def _stream_mock(
        self,
        prompt: str,
        model: str,
        **kwargs,
    ) -> AsyncGenerator[str, None]:
        """Mock 实现"""
        response = f"Mock response to: {prompt[:50]}..."
        for word in response.split():
            await asyncio.sleep(0.01)
            yield word + " "

    async def _stream_claude(
        self,
        prompt: str,
        model: str,
        **kwargs,
    ) -> AsyncGenerator[str, None]:
        """Claude API 流式"""
        try:
            import anthropic

            client = anthropic.AsyncAnthropic()
            async with client.messages.stream(
                model=model,
                max_tokens=kwargs.get("max_tokens", 1024),
                messages=[{"role": "user", "content": prompt}],
            ) as stream:
                async for text in stream.text_stream:
                    yield text
        except ImportError:
            # Fallback to mock
            async for chunk in self._stream_mock(prompt, model):
                yield chunk
        except Exception as e:
            # API 错误 - 抛到用户层处理
            raise RuntimeError(f"Claude API error: {e}")

    async def _stream_gemini(
        self,
        prompt: str,
        model: str,
        **kwargs,
    ) -> AsyncGenerator[str, None]:
        """Gemini API 流式"""
        try:
            import google.generativeai as genai

            gen_model = genai.GenerativeModel(model)
            response = await gen_model.generate_content_async(
                prompt,
                stream=True,
            )
            async for chunk in response:
                if chunk.text:
                    yield chunk.text
        except ImportError:
            async for chunk in self._stream_mock(prompt, model):
                yield chunk

    async def _stream_openai(
        self,
        prompt: str,
        model: str,
        **kwargs,
    ) -> AsyncGenerator[str, None]:
        """OpenAI API 流式"""
        try:
            import openai

            client = openai.AsyncOpenAI()
            stream = await client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                stream=True,
            )
            async for chunk in stream:
                # 安全访问 choices
                if chunk.choices and len(chunk.choices) > 0:
                    delta = chunk.choices[0].delta
                    if delta and delta.content:
                        yield delta.content
        except ImportError:
            async for chunk in self._stream_mock(prompt, model):
                yield chunk
        except Exception as e:
            raise RuntimeError(f"OpenAI API error: {e}")

    async def stream_to_string(
        self,
        prompt: str,
        model: str,
        **kwargs,
    ) -> str:
        """流式转完整字符串"""
        chunks = []
        async for chunk in self.stream(prompt, model, **kwargs):
            chunks.append(chunk)
        return "".join(chunks)

    async def stream_with_callback(
        self,
        prompt: str,
        model: str,
        on_chunk: Callable[[str], None],
        **kwargs,
    ) -> str:
        """带回调的流式"""
        full_text = ""
        async for chunk in self.stream(prompt, model, **kwargs):
            on_chunk(chunk)
            full_text += chunk
        return full_text

    async def stream_with_metrics(
        self,
        prompt: str,
        model: str,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        带指标的流式

        Note:
            token_count 目前是基于空格分割的估算值 (Word Count)，
            不是精确的 Token 数量。
        """
        import time

        start = time.time()
        chunks = []
        token_count = 0

        async for chunk in self.stream(prompt, model, **kwargs):
            chunks.append(chunk)
            token_count += len(chunk.split())

        return {
            "text": "".join(chunks),
            "metrics": {
                "tokens": token_count,
                "latency_ms": (time.time() - start) * 1000,
            },
        }

    async def stream_with_timeout(
        self,
        prompt: str,
        model: str,
        timeout: float,
        **kwargs,
    ) -> AsyncGenerator[str, None]:
        """
        带超时的流式

        Args:
            timeout: 总执行超时时间 (秒)。如果流式生成总时间超过此值，将抛出异常。
        """

        try:
            async with asyncio.timeout(timeout):
                async for chunk in self._collect_stream(prompt, model, **kwargs):
                    yield chunk
        except asyncio.TimeoutError:
            raise StreamTimeoutError(f"Stream timed out after {timeout}s")

    async def _collect_stream(
        self,
        prompt: str,
        model: str,
        **kwargs,
    ) -> AsyncGenerator[str, None]:
        """辅助方法: 收集流"""
        async for chunk in self.stream(prompt, model, **kwargs):
            yield chunk

    async def stream_with_interruption(
        self,
        prompt: str,
        model: str,
        interrupt_at: int,
        **kwargs,
    ) -> AsyncGenerator[str, None]:
        """可中断的流式 (测试用)"""
        count = 0
        async for chunk in self.stream(prompt, model, **kwargs):
            count += 1
            if count >= interrupt_at:
                raise InterruptedError("Stream interrupted for testing")
            yield chunk
    async def stream_with_thinking(
        self,
        prompt: str,
        model: str,
        on_thinking: Callable[[str], None] = None,
        on_content: Callable[[str], None] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """带思考过程可视化的流式"""
        import time
        start = time.time()
        first_token_time = None
        chunks = []
        thinking_shown = False

        if on_thinking:
            on_thinking("🤔 Thinking...")
            thinking_shown = True

        async for chunk in self.stream(prompt, model, **kwargs):
            if first_token_time is None:
                first_token_time = time.time()
                if thinking_shown and on_thinking:
                    on_thinking("")
            chunks.append(chunk)
            if on_content:
                on_content(chunk)

        end = time.time()
        ttft = (first_token_time - start) * 1000 if first_token_time else 0
        return {
            "text": "".join(chunks),
            "metrics": {"ttft_ms": ttft, "total_latency_ms": (end - start) * 1000, "tokens": sum(len(c.split()) for c in chunks)},
        }

    async def stream_as_sse(
        self,
        prompt: str,
        model: str,
        **kwargs,
    ) -> AsyncGenerator[str, None]:
        """以 SSE 格式输出"""
        import time
        import json
        yield f"event: start\ndata: {json.dumps({'model': model, 'timestamp': time.time()})}\n\n"
        first_token = True
        async for chunk in self.stream(prompt, model, **kwargs):
            if first_token:
                yield f"event: first_token\ndata: {json.dumps({'ttft_ms': 0})}\n\n"
                first_token = False
            escaped = chunk.replace("\n", "\\n")
            yield f"data: {escaped}\n\n"
        yield f"event: done\ndata: {json.dumps({'status': 'complete'})}\n\n"


class SSEFormatter:
    """SSE 格式化工具"""
    @staticmethod
    def format_event(event_type: str, data: Any) -> str:
        import json
        data_str = json.dumps(data) if isinstance(data, dict) else str(data).replace("\n", "\\n")
        return f"event: {event_type}\ndata: {data_str}\n\n" if event_type else f"data: {data_str}\n\n"

    @staticmethod
    def format_chunk(text: str) -> str:
        return f"data: {text.replace(chr(10), chr(92) + 'n')}\n\n"

    @staticmethod
    def format_done() -> str:
        return "event: done\ndata: {}\n\n"


__all__ = ["StreamingLLM", "StreamTimeoutError", "SSEFormatter"]

