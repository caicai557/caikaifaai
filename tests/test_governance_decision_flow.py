"""
Tests for decision approval flow.
"""


def test_requires_decision_approval():
    from council.governance.gateway import GovernanceGateway, DecisionType

    gateway = GovernanceGateway()

    assert gateway.requires_decision_approval(DecisionType.SECURITY_EXCEPTION) is True
    assert gateway.requires_decision_approval(DecisionType.MODEL_SELECTION) is False


def test_create_decision_request():
    from council.governance.gateway import (
        GovernanceGateway,
        DecisionType,
        ApprovalKind,
    )

    gateway = GovernanceGateway()
    request = gateway.create_decision_request(
        decision_type=DecisionType.ARCHITECTURE_CHANGE,
        description="Switch orchestration topology",
        affected_resources=["orchestration", "agents"],
        rationale="Reduce routing latency",
    )

    assert request.request_id.startswith("REQ-")
    assert request.request_kind == ApprovalKind.DECISION
    assert request.decision_type == DecisionType.ARCHITECTURE_CHANGE
