"""
Tests for Sub-Agent Delegation Framework
- AgentRegistry
- DelegationManager
"""

import pytest
from council.agents.base_agent import (
    BaseAgent,
    ThinkResult,
    Vote,
    VoteDecision,
    ExecuteResult,
)
from council.orchestration.agent_registry import AgentRegistry
from council.orchestration.delegation import (
    DelegationManager,
    DelegationStatus,
    MaxDepthExceededError,
    DelegationNotAllowedError,
)


# Test Agent Implementation
class MockAgent(BaseAgent):
    """Mock Agent for testing"""

    def think(self, task, context=None):
        return ThinkResult(analysis=f"Mock analysis: {task}")

    def vote(self, proposal, context=None):
        return Vote(
            agent_name=self.name,
            decision=VoteDecision.APPROVE,
            confidence=0.8,
            rationale="Mock vote",
        )

    def execute(self, task, plan=None):
        return ExecuteResult(
            success=True, output=f"Mock executed: {task}", changes_made=[f"Did {task}"]
        )


# ============================================================
# AgentRegistry Tests
# ============================================================


class TestAgentRegistry:
    """AgentRegistry 测试"""

    @pytest.fixture
    def registry(self):
        return AgentRegistry()

    @pytest.fixture
    def mock_agent(self):
        return MockAgent(
            name="test_agent", system_prompt="Test agent", allow_delegation=True
        )

    def test_register_and_get(self, registry, mock_agent):
        """测试注册和获取"""
        registry.register(mock_agent, capabilities=["coding"])

        agent = registry.get("test_agent")
        assert agent is not None
        assert agent.name == "test_agent"

    def test_register_with_capabilities(self, registry, mock_agent):
        """测试带能力的注册"""
        registry.register(mock_agent, capabilities=["coding", "debugging"])

        coders = registry.find_by_capability("coding")
        assert len(coders) == 1
        assert coders[0].name == "test_agent"

    def test_find_by_capability(self, registry):
        """测试按能力查找"""
        agent1 = MockAgent("coder", "Coder")
        agent2 = MockAgent("reviewer", "Reviewer")

        registry.register(agent1, capabilities=["coding"])
        registry.register(agent2, capabilities=["review"])

        coders = registry.find_by_capability("coding")
        reviewers = registry.find_by_capability("review")

        assert len(coders) == 1
        assert len(reviewers) == 1
        assert coders[0].name == "coder"

    def test_list_available(self, registry, mock_agent):
        """测试列出可用 Agent"""
        registry.register(mock_agent)

        available = registry.list_available()
        assert "test_agent" in available

    def test_unregister(self, registry, mock_agent):
        """测试注销"""
        registry.register(mock_agent)
        assert registry.get("test_agent") is not None

        registry.unregister("test_agent")
        assert registry.get("test_agent") is None

    def test_can_delegate_to(self, registry):
        """测试委托检查"""
        delegator = MockAgent("delegator", "D", allow_delegation=True)
        worker = MockAgent("worker", "W")

        registry.register(delegator)
        registry.register(worker)

        can, reason = registry.can_delegate_to(delegator, "worker")
        assert can is True

    def test_cannot_delegate_if_not_allowed(self, registry):
        """测试不允许委托时"""
        delegator = MockAgent("delegator", "D", allow_delegation=False)
        worker = MockAgent("worker", "W")

        registry.register(delegator)
        registry.register(worker)

        can, reason = registry.can_delegate_to(delegator, "worker")
        assert can is False
        assert "allow_delegation" in reason


# ============================================================
# DelegationManager Tests
# ============================================================


class TestDelegationManager:
    """DelegationManager 测试"""

    @pytest.fixture
    def setup(self):
        """设置测试环境"""
        registry = AgentRegistry()

        orchestrator = MockAgent(
            "orchestrator",
            "Orchestrator",
            allow_delegation=True,
            max_delegation_depth=3,
        )
        coder = MockAgent("coder", "Coder")
        reviewer = MockAgent("reviewer", "Reviewer")

        registry.register(orchestrator, ["planning"])
        registry.register(coder, ["coding"])
        registry.register(reviewer, ["review"])

        dm = DelegationManager(registry)

        return {
            "registry": registry,
            "dm": dm,
            "orchestrator": orchestrator,
            "coder": coder,
            "reviewer": reviewer,
        }

    def test_successful_delegation(self, setup):
        """测试成功委托"""
        result = setup["dm"].delegate(
            task="实现登录功能", from_agent=setup["orchestrator"], to_agent_name="coder"
        )

        assert result.status == DelegationStatus.SUCCESS
        assert result.result is not None
        assert result.result.success is True

    def test_delegation_not_allowed(self, setup):
        """测试不允许委托"""
        no_delegate_agent = MockAgent("no_delegate", "ND", allow_delegation=False)
        setup["registry"].register(no_delegate_agent)

        with pytest.raises(DelegationNotAllowedError):
            setup["dm"].delegate(
                task="Test", from_agent=no_delegate_agent, to_agent_name="coder"
            )

    def test_max_depth_exceeded(self, setup):
        """测试深度限制"""
        setup["dm"]._current_chain = ["a", "b", "c"]  # 模拟深度 3

        with pytest.raises(MaxDepthExceededError):
            setup["dm"].delegate(
                task="Test", from_agent=setup["orchestrator"], to_agent_name="coder"
            )

    def test_get_stats(self, setup):
        """测试统计"""
        setup["dm"].delegate(
            task="Test 1", from_agent=setup["orchestrator"], to_agent_name="coder"
        )

        stats = setup["dm"].get_stats()
        assert stats["total"] == 1
        assert stats["success"] == 1
