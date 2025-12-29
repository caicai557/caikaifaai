#!/usr/bin/env python3
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def write_text(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")


def update_base_agent() -> None:
    path = ROOT / "council" / "agents" / "base_agent.py"
    content = read_text(path)
    if "governance_gateway" not in content:
        content = content.replace(
            "max_delegation_depth: int = 3,\n    ):",
            'max_delegation_depth: int = 3,\n        governance_gateway: Optional["GovernanceGateway"] = None,\n    ):',
            1,
        )
        content = content.replace(
            "max_delegation_depth: 最大委托链深度",
            "max_delegation_depth: 最大委托链深度\n"
            "            governance_gateway: 可选的治理网关 (关键决策审批)",
            1,
        )
        content = content.replace(
            "self._current_delegation_depth = 0\n\n        # API key detection",
            "self._current_delegation_depth = 0\n"
            "        self.governance_gateway = governance_gateway\n\n"
            "        # API key detection",
            1,
        )

        marker = (
            "    def _has_llm(self) -> bool:\n"
            '        """检查是否有可用的 LLM API"""\n'
            "        return self._has_gemini or self._has_openai\n"
        )
        insert = (
            marker
            + """
    def request_decision_approval(
        self,
        decision_type: "DecisionType",
        description: str,
        affected_resources: List[str],
        rationale: str,
        council_decision: Optional[Dict[str, Any]] = None,
        requestor: Optional[str] = None,
        timeout_seconds: int = 300,
    ) -> bool:
        \"\"\"
        请求关键决策审批
        \"\"\"
        from council.governance.gateway import GovernanceGateway, DecisionType

        if not isinstance(decision_type, DecisionType):
            raise ValueError("decision_type must be a DecisionType")

        if self.governance_gateway is None:
            self.governance_gateway = GovernanceGateway()

        if not self.governance_gateway.requires_decision_approval(decision_type):
            return True

        request = self.governance_gateway.create_decision_request(
            decision_type=decision_type,
            description=description,
            affected_resources=affected_resources,
            rationale=rationale,
            council_decision=council_decision,
            requestor=requestor or self.name,
        )
        approved = self.governance_gateway.wait_for_approval(
            request,
            timeout_seconds=timeout_seconds,
        )
        self.add_to_history(
            {
                "action": "decision_approval",
                "decision_type": decision_type.value,
                "approved": approved,
                "request_id": request.request_id,
            }
        )
        return approved
"""
        )
        if marker not in content:
            raise ValueError("BaseAgent _has_llm marker not found")
        content = content.replace(marker, insert, 1)

    write_text(path, content)


def update_orchestrator() -> None:
    path = ROOT / "council" / "agents" / "orchestrator.py"
    content = read_text(path)
    if "DecisionType" not in content:
        content = content.replace(
            "from council.orchestration.ledger import DualLedger\n",
            "from council.orchestration.ledger import DualLedger\n"
            "from council.governance.gateway import DecisionType, GovernanceGateway\n",
            1,
        )

    content = content.replace(
        'def __init__(self, model: str = "gemini-2.0-flash"):',
        'def __init__(self, model: str = "gemini-2.0-flash", '
        "governance_gateway: Optional[GovernanceGateway] = None):",
        1,
    )

    content = content.replace(
        "model=model,",
        "model=model,\n            governance_gateway=governance_gateway,",
        1,
    )

    agents_block = """    AVAILABLE_AGENTS = {
        "Architect": ["architecture", "design", "system", "structure", "api"],
        "Coder": ["implement", "code", "test", "function", "class", "bug", "fix"],
        "SecurityAuditor": [
            "security",
            "audit",
            "vulnerability",
            "compliance",
            "permission",
        ],
    }
"""
    if "DECISION_KEYWORDS" not in content:
        decision_block = (
            agents_block
            + """
    DECISION_KEYWORDS = {
        DecisionType.ARCHITECTURE_CHANGE: [
            "architecture",
            "re-architect",
            "redesign",
            "migration",
            "migrate",
            "架构",
            "重构",
            "重写",
        ],
        DecisionType.DEPLOY_STRATEGY: [
            "deploy",
            "release",
            "rollout",
            "canary",
            "blue-green",
            "上线",
            "发布",
        ],
        DecisionType.SECURITY_EXCEPTION: [
            "exception",
            "bypass",
            "skip security",
            "disable auth",
            "临时放开",
            "忽略安全",
        ],
        DecisionType.DATA_RETENTION: [
            "retention",
            "archive",
            "purge",
            "data retention",
            "保留策略",
            "删除数据",
        ],
        DecisionType.MODEL_SELECTION: [
            "model selection",
            "routing",
            "router",
            "model",
            "模型选择",
            "模型",
        ],
    }
"""
        )
        if agents_block not in content:
            raise ValueError("AVAILABLE_AGENTS block not found")
        content = content.replace(agents_block, decision_block, 1)

    marker = "        return goal\n\n    def dispatch(self, subtask: SubTask, agent: BaseAgent) -> ExecuteResult:"
    insert = """        return goal\n\n    def _infer_decision_types(self, goal: str) -> List[DecisionType]:
        \"\"\"从任务描述中识别关键决策类型\"\"\"
        goal_lower = goal.lower()
        decisions: List[DecisionType] = []
        for decision_type, keywords in self.DECISION_KEYWORDS.items():
            if any(keyword in goal_lower for keyword in keywords):
                decisions.append(decision_type)
        return decisions

    def _request_decision_approvals(self, goal: str) -> Optional[ExecuteResult]:
        \"\"\"对关键决策进行审批请求\"\"\"
        decisions = self._infer_decision_types(goal)
        for decision_type in decisions:
            description = f"关键决策: {decision_type.value}"
            approved = self.request_decision_approval(
                decision_type=decision_type,
                description=description,
                affected_resources=["orchestrator"],
                rationale="触发关键决策关键词，需要人工确认",
            )
            if not approved:
                return ExecuteResult(
                    success=False,
                    output=f"决策需要人工审批: {decision_type.value}",
                    errors=[f"Approval required for decision: {decision_type.value}"],
                )
        return None

    def dispatch(self, subtask: SubTask, agent: BaseAgent) -> ExecuteResult:"""
    if marker not in content:
        raise ValueError("Dispatch marker not found for decision insertion")
    content = content.replace(marker, insert, 1)

    content = content.replace(
        "        decomposition = self.decompose(task)\n",
        "        decision_result = self._request_decision_approvals(task)\n"
        "        if decision_result:\n"
        "            return decision_result\n\n"
        "        decomposition = self.decompose(task)\n",
        1,
    )

    write_text(path, content)


def add_tests() -> None:
    path = ROOT / "tests" / "test_orchestrator_decision_gate.py"
    content = """\"\"\"
Tests for orchestrator decision approval gating.
\"\"\"


def test_orchestrator_blocks_without_approval():
    from council.agents.orchestrator import Orchestrator

    orch = Orchestrator()
    result = orch.execute(\"进行架构重构\")

    assert result.success is False
    assert \"审批\" in result.output


def test_orchestrator_allows_with_approval_callback():
    from council.agents.orchestrator import Orchestrator
    from council.governance.gateway import GovernanceGateway

    gateway = GovernanceGateway()
    gateway.set_approval_callback(lambda _req: True)

    orch = Orchestrator(governance_gateway=gateway)
    result = orch.execute(\"进行架构重构\")

    assert result.success is True
"""
    if not path.exists():
        write_text(path, content)


def main() -> None:
    update_base_agent()
    update_orchestrator()
    add_tests()


if __name__ == "__main__":
    main()
