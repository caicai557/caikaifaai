"""
The First Council - End-to-End System/Governance Verification
Simulates a full Council meeting without requiring live API keys.
"""

import sys
import os
import asyncio
import logging
from typing import List, Dict, Any, Type

# Add project root
sys.path.append(os.getcwd())

from council.core.llm_client import LLMClient
from council.dev_orchestrator import DevOrchestrator
from council.protocol.schema import MinimalVote, MinimalThinkResult, VoteEnum

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(name)s - %(message)s")
logger = logging.getLogger("FirstCouncil")


class SimulatedLLMClient(LLMClient):
    """
    A high-fidelity simulator that returns structured Pydantic objects
    based on the Agent Persona and Request Type.
    """

    def completion(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """Simulate text completion"""
        prompt = messages[-1]["content"]
        # Basic parsing to identify agent/intent
        if "Decompose" in prompt or "task" in prompt:
            return "I will decompose this task into subtasks."
        return "Simulated response."

    def structured_completion(
        self, messages: List[Dict[str, str]], response_model: Type, **kwargs
    ) -> Any:
        """Simulate structured output based on the target schema and prompt context"""

        system_msg = next((m["content"] for m in messages if m["role"] == "system"), "")
        prompt = messages[-1]["content"]

        logger.info(
            f"⚡ [LLM Call] Schema: {response_model.__name__} | Persona: {system_msg[:20]}..."
        )

        # 1. Orchestrator Logic
        if "Council Chairman" in system_msg:
            # Orchestrator doesn't use structured output for decomposition yet (it uses text parsing in current impl)
            # But if it did, we'd handle it here.
            pass

        # 2. Architect Logic
        if "Architect" in system_msg:
            if response_model == MinimalThinkResult:
                return MinimalThinkResult(
                    summary="The proposed auth refactor requires updating the User schema and JWT middleware.",
                    concerns=[
                        "Backward compatibility with legacy tokens",
                        "Session invalidation",
                    ],
                    suggestions=[
                        "Implement dual-write for migration",
                        "Use RS256 signing",
                    ],
                    confidence=0.9,
                    perspective="architecture",
                )
            if response_model == MinimalVote:
                return MinimalVote(
                    vote=VoteEnum.APPROVE_WITH_CHANGES,
                    confidence=0.85,
                    risks=["maint"],
                    blocking_reason=None,
                )

        # 3. Security Auditor Logic
        if "SecurityAuditor" in system_msg:
            if response_model == MinimalThinkResult:
                return MinimalThinkResult(
                    summary="JWT implementations are prone to 'none' algo attacks and secret leakage.",
                    concerns=[
                        "Secret key management",
                        "Token expiration enforcement",
                        "Replay attacks",
                    ],
                    suggestions=[
                        "Use hardware security module",
                        "Enforce strict expiration",
                    ],
                    confidence=0.95,
                    perspective="security",
                )
            if response_model == MinimalVote:
                return MinimalVote(
                    vote=VoteEnum.HOLD,
                    confidence=0.9,
                    risks=["sec"],
                    blocking_reason="Need verification of key storage mechanism.",
                )

        # 4. Coder Logic
        if "Coder" in system_msg:
            if response_model == MinimalThinkResult:
                return MinimalThinkResult(
                    summary="I will create `auth/jwt_handler.py` and update `middleware.py`.",
                    concerns=["Test coverage for edge cases"],
                    suggestions=["Use PyJWT library"],
                    confidence=0.8,
                    perspective="implementation",
                )
            if response_model == MinimalVote:
                return MinimalVote(
                    vote=VoteEnum.APPROVE,
                    confidence=0.9,
                    risks=[],
                    blocking_reason=None,
                )

        # Fallback
        return response_model()


async def main():
    print("\n🏛️  THE FIRST COUNCIL MEETING (Simulation) 🏛️\n")
    print("Agenda: Refactor Authentication Module to use JWT\n")

    # 1. Initialize Council with Simulator
    simulator = SimulatedLLMClient()
    orchestrator = DevOrchestrator(llm_client=simulator)

    # 2. Mock the Orchestrator's internal Task Classification/Decomposition
    # (Since Orchestrator.decompose still relies on text parsing/logic we might need to mock execution steps directly
    # OR rely on the fact that Orchestrator calls Agents who call LLM)

    print("--- [Step 1] Orchestrator Planning ---")
    # For this verification, we manually trigger the agents to see them 'think' and 'vote'
    # mimicking what the Orchestrator would do in `dispatch` loop.

    task_description = "Refactor Authentication Module to use JWT"

    # Architect Analysis
    print("\n🧐 Architect is Thinking...")
    arch_result = orchestrator.agents["Architect"].think_structured(task_description)
    print(f"   Summary: {arch_result.summary}")
    print(f"   Concerns: {arch_result.concerns}")

    # Security Audit
    print("\n🛡️  Security Auditor is Analyzing...")
    sec_result = orchestrator.agents["SecurityAuditor"].think_structured(
        task_description
    )
    print(f"   Summary: {sec_result.summary}")
    print(f"   Risks Identified: {sec_result.concerns}")

    # Coder Planning
    print("\n💻 Coder is Planning...")
    coder_result = orchestrator.agents["Coder"].think_structured(task_description)
    print(f"   Plan: {coder_result.summary}")

    # 3. Governance / Voting Simulation
    print("\n--- [Step 2] Council Voting on Implementation Plan ---")
    proposal = f"Implementation Plan: {coder_result.summary}. Architecture: {arch_result.summary}"

    print("\n🗳️  Casting Votes...")
    v1 = orchestrator.agents["Architect"].vote_structured(proposal)
    print(f"   Architect: {v1.vote.name} (Risks: {v1.risks})")

    v2 = orchestrator.agents["SecurityAuditor"].vote_structured(proposal)
    print(f"   SecurityAuditor: {v2.vote.name} (Blocking: {v2.blocking_reason})")

    v3 = orchestrator.agents["Coder"].vote_structured(proposal)
    print(f"   Coder: {v3.vote.name}")

    # 4. Success Criteria
    print("\n--- Verification Results ---")
    if (
        arch_result.perspective == "architecture"
        and sec_result.perspective == "security"
        and v2.vote == VoteEnum.HOLD
    ):
        print("✅ Council Behavior Verified:")
        print("   - Agents demonstrated distinct personas")
        print("   - Structured outputs were correctly parsed")
        print(
            "   - Security Auditor correctly blocked potentially unsafe plan (Simulation)"
        )
    else:
        print(
            f"❌ Verification Failed. State: Arch={arch_result.perspective}, Sec={sec_result.perspective}, Vote={v2.vote}"
        )
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
