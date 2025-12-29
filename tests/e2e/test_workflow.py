"""
E2E Tests - End-to-End Workflow Tests

测试完整工作流:
1. TaskClassifier → 模型路由
2. AgentRegistry → Agent 发现
3. DelegationManager → 委托执行
4. WaldConsensus → 共识裁决
"""

import pytest
from council.orchestration import (
    AgentRegistry,
    DelegationManager,
    DelegationStatus,
)
from council.orchestration.task_classifier import (
    TaskClassifier,
    RecommendedModel,
    TaskType,
)
from council.agents.base_agent import (
    BaseAgent,
    ThinkResult,
    Vote,
    VoteDecision,
    ExecuteResult,
)
from council.facilitator.wald_consensus import WaldConsensus, WaldConfig


# =============================================================
# Mock Agent for E2E Testing
# =============================================================


class MockE2EAgent(BaseAgent):
    """E2E 测试用 Mock Agent"""

    def __init__(self, name: str, role: str, **kwargs):
        super().__init__(name=name, system_prompt=f"You are a {role} agent.", **kwargs)
        self.role = role
        self.execution_log = []

    def think(self, task, context=None):
        self.execution_log.append(("think", task))
        return ThinkResult(
            analysis=f"[{self.role}] Analyzed: {task}",
            concerns=["Minor concern"],
            suggestions=["Recommendation"],
            confidence=0.85,
        )

    def vote(self, proposal, context=None):
        self.execution_log.append(("vote", proposal))
        return Vote(
            agent_name=self.name,
            decision=VoteDecision.APPROVE,
            confidence=0.9,
            rationale=f"[{self.role}] Approved with confidence",
        )

    def execute(self, task, plan=None):
        self.execution_log.append(("execute", task))
        return ExecuteResult(
            success=True,
            output=f"[{self.role}] Executed: {task}",
            changes_made=[f"Changed by {self.role}"],
        )


# =============================================================
# E2E Test: Complete Workflow
# =============================================================


class TestE2EWorkflow:
    """端到端工作流测试"""

    @pytest.fixture
    def setup_council(self):
        """设置完整的理事会环境"""
        # 1. 创建 Registry
        registry = AgentRegistry()

        # 2. 创建各类 Agent
        orchestrator = MockE2EAgent(
            "orchestrator",
            "Orchestrator",
            allow_delegation=True,
            max_delegation_depth=3,
        )
        architect = MockE2EAgent("architect", "Architect")
        coder = MockE2EAgent("coder", "Coder")
        reviewer = MockE2EAgent("reviewer", "Reviewer")

        # 3. 注册 Agent
        registry.register(orchestrator, ["planning", "orchestration"])
        registry.register(architect, ["architecture", "design"])
        registry.register(coder, ["coding", "debugging"])
        registry.register(reviewer, ["review", "security"])

        # 4. 创建 DelegationManager
        delegation_manager = DelegationManager(registry)

        # 5. 创建 TaskClassifier
        task_classifier = TaskClassifier()

        return {
            "registry": registry,
            "delegation_manager": delegation_manager,
            "task_classifier": task_classifier,
            "orchestrator": orchestrator,
            "architect": architect,
            "coder": coder,
            "reviewer": reviewer,
        }

    def test_full_workflow(self, setup_council):
        """测试完整工作流: 分类 → 路由 → 委托 → 执行"""
        ctx = setup_council

        # Step 1: 任务分类
        task = "实现用户登录功能"
        result = ctx["task_classifier"].classify(task)

        assert result.task_type == TaskType.CODING
        assert result.recommended_model == RecommendedModel.CLAUDE_SONNET

        # Step 2: 查找合适的 Agent
        coders = ctx["registry"].find_by_capability("coding")
        assert len(coders) == 1
        assert coders[0].name == "coder"

        # Step 3: 执行委托
        delegation_result = ctx["delegation_manager"].delegate(
            task=task,
            from_agent=ctx["orchestrator"],
            to_agent_name="coder",
        )

        assert delegation_result.status == DelegationStatus.SUCCESS
        assert delegation_result.result.success is True

        # Step 4: 验证执行日志
        assert ("execute", task) in ctx["coder"].execution_log

    def test_model_routing_accuracy(self, setup_council):
        """测试模型路由准确性"""
        tc = setup_council["task_classifier"]

        test_cases = [
            ("设计系统架构", TaskType.PLANNING, RecommendedModel.GPT_CODEX),
            ("实现登录功能", TaskType.CODING, RecommendedModel.CLAUDE_SONNET),
            ("审查代码安全", TaskType.REVIEW, RecommendedModel.GEMINI_PRO),
            ("重构核心模块", TaskType.REFACTORING, RecommendedModel.CLAUDE_OPUS),
            ("写单元测试", TaskType.TESTING, RecommendedModel.GEMINI_FLASH),
        ]

        for task, expected_type, expected_model in test_cases:
            result = tc.classify(task)
            assert result.task_type == expected_type, f"Failed for task: {task}"
            assert result.recommended_model == expected_model, (
                f"Failed for task: {task}"
            )

    def test_delegation_chain(self, setup_council):
        """测试委托链追踪"""
        dm = setup_council["delegation_manager"]

        # 执行多次委托
        for task in ["Task 1", "Task 2", "Task 3"]:
            dm.delegate(
                task=task,
                from_agent=setup_council["orchestrator"],
                to_agent_name="coder",
            )

        # 验证统计
        stats = dm.get_stats()
        assert stats["total"] == 3
        assert stats["success"] == 3
        assert stats["success_rate"] == 100.0

    def test_wald_consensus(self):
        """测试 Wald 共识算法"""
        config = WaldConfig(
            upper_limit=0.95,
            lower_limit=0.30,
            prior_approve=0.70,
        )
        wald = WaldConsensus(config)

        # 模拟投票
        votes = [
            {"decision": "approve", "confidence": 0.9},
            {"decision": "approve", "confidence": 0.85},
            {"decision": "approve", "confidence": 0.95},
        ]

        result = wald.evaluate(votes)
        # 高置信度批准应该自动提交
        assert result.decision.value in ["auto_commit", "hold_for_human"]


# =============================================================
# E2E Test: Error Handling
# =============================================================


class TestE2EErrorHandling:
    """端到端错误处理测试"""

    def test_delegation_to_nonexistent_agent(self):
        """测试委托给不存在的 Agent"""
        registry = AgentRegistry()
        dm = DelegationManager(registry)

        agent = MockE2EAgent("test", "Test", allow_delegation=True)
        registry.register(agent)

        with pytest.raises(Exception):
            dm.delegate(
                task="Test",
                from_agent=agent,
                to_agent_name="nonexistent",
            )

    def test_max_depth_protection(self):
        """测试最大深度保护"""
        registry = AgentRegistry()

        agent = MockE2EAgent(
            "test",
            "Test",
            allow_delegation=True,
            max_delegation_depth=2,
        )
        registry.register(agent)

        dm = DelegationManager(registry, global_max_depth=2)
        dm._current_chain = ["a", "b"]  # 模拟已有深度

        from council.orchestration.delegation import MaxDepthExceededError

        with pytest.raises(MaxDepthExceededError):
            dm.delegate(
                task="Test",
                from_agent=agent,
                to_agent_name="test",
            )
