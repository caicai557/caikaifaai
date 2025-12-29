#!/usr/bin/env python3
"""
Streaming Demo

演示如何使用流式 LLM 响应
"""

import asyncio
from council.streaming import StreamingLLM


async def main():
    # 创建流式客户端
    streamer = StreamingLLM()

    print("=== Streaming Demo ===")
    print()

    # 使用 mock 模式演示
    print("Streaming response:")
    async for chunk in streamer.stream(
        prompt="Explain what is Council framework",
        model="mock",  # 使用 mock 避免需要 API
    ):
        print(chunk, end="", flush=True)

    print()
    print()

    # 带指标的流式
    result = await streamer.stream_with_metrics(
        prompt="What is TDD?",
        model="mock",
    )

    print(f"Response: {result['text']}")
    print(f"Tokens: {result['metrics']['tokens']}")
    print(f"Latency: {result['metrics']['latency_ms']:.2f}ms")


if __name__ == "__main__":
    asyncio.run(main())
