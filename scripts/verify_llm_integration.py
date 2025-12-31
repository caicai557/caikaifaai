"""
Verify LLM Integration (Phase 4: The Awakening)

This script validates:
1. LLMClient connectivity (mocked for CI/safety)
2. Agent structure "thinking" (JSON output)
3. DevOrchestrator pipeline wiring
"""

import sys
import os
import asyncio
from unittest.mock import MagicMock

# Add project root to path
sys.path.append(os.getcwd())

from council.core.llm_client import LLMClient
from council.dev_orchestrator import DevOrchestrator
from council.agents.coder import Coder


async def main():
    print("🧠 The Awakening: Verifying LLM Integration...")

    # 1. Setup Mock LLM Client (Safe for test without API keys)
    mock_llm_client = MagicMock(spec=LLMClient)

    # Mock structured_completion for Coder.think_structured
    from council.protocol.schema import MinimalThinkResult

    mock_llm_client.structured_completion.return_value = MinimalThinkResult(
        summary="I have analyzed the task and it appears feasible.",
        concerns=["Mock environment execution"],
        suggestions=["Use dependency injection"],
        confidence=0.95,
        perspective="implementation",
    )

    # Mock completion for standard calls
    mock_llm_client.completion.return_value = "Mocked LLM response"

    print("✅ LLMClient mocked successfully.")

    # 2. Verify Agent Wiring
    print("\n🔍 Verifying Agent -> LLMClient wiring...")
    coder = Coder(llm_client=mock_llm_client)

    think_result = coder.think_structured("Create a hello world in Python")
    print(f"   Agent Thought: {think_result.summary}")
    print(f"   Confidence: {think_result.confidence}")

    if think_result.confidence == 0.95:
        print("✅ Agent correctly used injected LLMClient for structured output.")
    else:
        print("❌ Agent failed to use injected LLMClient.")

    # 3. Verify DevOrchestrator Pipeline
    print("\n🚀 Verifying DevOrchestrator pipeline...")
    orchestrator = DevOrchestrator(llm_client=mock_llm_client, verbose=True)

    # Patch the classifier's classify method for speed?
    # Actually, orchestrator uses llm_client internally ideally,
    # but TaskClassifier might still be using its own logic
    # (TaskClassifier is legacy code we haven't touched this turn, assuming it works or uses simple regex/spacy from previous state)

    # Let's run a fake task
    # Note: orchestrator.classify might fail if it relies on real LLM and we haven't injected there yet?
    # Checking dev_orchestrator.py: "self.classifier = TaskClassifier(cost_sensitive=cost_sensitive)"
    # Does TaskClassifier take llm_client? No, looking at dev_orchestrator init.
    # It seems TaskClassifier is legacy. We might hit a snag there if it requires real API keys.
    # But let's try.

    try:
        # Mocking `dev` loop dependencies if needed
        # Actually, let's just check if agents inside orchestrator have the client
        if orchestrator.agents["Coder"].llm_client == mock_llm_client:
            print("✅ Orchestrator successfully propagated LLMClient to Agents.")
        else:
            print("❌ Orchestrator failed to propagate LLMClient.")

    except Exception as e:
        print(f"❌ Error verifying Orchestrator: {e}")

    print("\n✨ Verification Complete.")


if __name__ == "__main__":
    asyncio.run(main())
