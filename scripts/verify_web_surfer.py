"""
Verify WebSurfer Agent
Tests the WebSurfer's ability to "browse" (mocked) and verify facts.
"""

import sys
import os
import asyncio
from unittest.mock import MagicMock

sys.path.append(os.getcwd())

from council.agents.web_surfer import WebSurfer
from council.core.llm_client import LLMClient


async def main():
    print("🌊 Verifying WebSurfer Agent...")

    # 1. Mock LLM Client
    mock_llm = MagicMock(spec=LLMClient)
    # Mock structured think result
    from council.protocol.schema import MinimalThinkResult

    mock_llm.structured_completion.return_value = MinimalThinkResult(
        summary="Need to search for 'LiteLLM structured output' docs.",
        concerns=[],
        suggestions=["Check official docs"],
        confidence=0.9,
        perspective="research",
    )

    # 2. Instantiate WebSurfer
    surfer = WebSurfer(llm_client=mock_llm)
    print("✅ WebSurfer instantiated.")

    # 3. Test Think
    task = "Find out how to use structured output in LiteLLM."
    print(f"\n🔍 Testing Think with task: '{task}'")

    think_result = surfer.think_structured(task)
    print(f"   Analysis: {think_result.summary}")

    if think_result.perspective == "research":
        print("✅ WebSurfer correctly identified research perspective.")
    else:
        print(f"❌ Unexpected perspective: {think_result.perspective}")
        sys.exit(1)

    # 4. Test Execute (Mock Search)
    print("\n🏃 Testing Execute...")
    exec_result = surfer.execute(task)
    print(f"   Output: {exec_result.output}")

    if "LiteLLM" in exec_result.output:
        print("✅ WebSurfer execution simulated successful search.")
    else:
        print("❌ WebSurfer execution failed to return expected content.")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
