"""
Tests for orchestrator decision approval gating.
"""


def test_orchestrator_blocks_without_approval():
    from council.agents.orchestrator import Orchestrator

    orch = Orchestrator()
    result = orch.execute("进行架构重构")

    assert result.success is False
    assert "审批" in result.output


def test_orchestrator_allows_with_approval_callback():
    from council.agents.orchestrator import Orchestrator
    from council.governance.gateway import GovernanceGateway

    gateway = GovernanceGateway()
    gateway.set_approval_callback(lambda _req: True)

    orch = Orchestrator(governance_gateway=gateway)
    result = orch.execute("进行架构重构")

    assert result.success is True
