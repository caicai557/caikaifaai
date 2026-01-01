"""
Tests for BaseAgent helpers.
"""

from typing import Optional, Dict, Any
import sys
import types


def _ensure_litellm_stub():
    if "litellm" not in sys.modules:
        stub = types.ModuleType("litellm")
        stub.completion = lambda *args, **kwargs: None
        sys.modules["litellm"] = stub


def _make_agent_class():
    _ensure_litellm_stub()
    from council.agents.base_agent import (
        BaseAgent,
        ThinkResult,
        Vote,
        VoteDecision,
        ExecuteResult,
    )

    class DummyAgent(BaseAgent):
        def think(
            self, task: str, context: Optional[Dict[str, Any]] = None
        ) -> ThinkResult:
            return ThinkResult(analysis="ok")

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
            return ExecuteResult(success=True, output="done")

    return DummyAgent


def test_has_llm_defaults_false(monkeypatch):
    DummyAgent = _make_agent_class()

    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    agent = DummyAgent(name="dummy", system_prompt="test")

    assert agent._has_llm() is False


def test_has_llm_true_with_env(monkeypatch):
    DummyAgent = _make_agent_class()

    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")

    agent = DummyAgent(name="dummy", system_prompt="test")

    assert agent._has_llm() is True
