"""
Tests for Orchestrator dispatch error handling.
"""

from typing import Optional, Dict, Any
import sys
import types


def _ensure_litellm_stub():
    if "litellm" not in sys.modules:
        stub = types.ModuleType("litellm")
        stub.completion = lambda *args, **kwargs: None
        sys.modules["litellm"] = stub


def _make_exploding_agent():
    _ensure_litellm_stub()
    from council.agents.base_agent import (
        BaseAgent,
        ThinkResult,
        Vote,
        VoteDecision,
        ExecuteResult,
    )

    class ExplodingAgent(BaseAgent):
        def think(
            self, task: str, context: Optional[Dict[str, Any]] = None
        ) -> ThinkResult:
            return ThinkResult(analysis="n/a")

        def vote(self, proposal: str, context: Optional[Dict[str, Any]] = None) -> Vote:
            return Vote(
                agent_name=self.name,
                decision=VoteDecision.HOLD,
                confidence=0.5,
                rationale="n/a",
            )

        def execute(
            self, task: str, plan: Optional[Dict[str, Any]] = None
        ) -> ExecuteResult:
            raise RuntimeError("boom")

    return ExplodingAgent


def test_orchestrator_dispatch_handles_exceptions():
    from council.agents.orchestrator import Orchestrator, SubTask

    ExplodingAgent = _make_exploding_agent()

    orch = Orchestrator()
    subtask = SubTask(
        id="ST-001",
        description="test",
        assigned_agent="Exploder",
        priority="P0",
    )

    result = orch.dispatch(
        subtask, ExplodingAgent(name="Exploder", system_prompt="test")
    )

    assert result.success is False
    assert subtask.status == "blocked"
    assert "执行代理失败" in result.output
    assert result.errors
