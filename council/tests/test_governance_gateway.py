"""
Unit tests for Governance Gateway (HITL)

Tests cover:
- requires_approval for high-risk actions
- Protected path detection
- Approval workflow (create, approve, reject)
"""

from council.governance.gateway import (
    GovernanceGateway,
    ApprovalRequest,
    ActionType,
    RiskLevel,
    HIGH_RISK_ACTIONS,
)


class TestRequiresApprovalHighRisk:
    """Tests for requires_approval based on action type risk"""

    def test_deploy_requires_approval(self):
        """DEPLOY action should always require approval"""
        gateway = GovernanceGateway()
        assert gateway.requires_approval(ActionType.DEPLOY) is True

    def test_database_requires_approval(self):
        """DATABASE action should always require approval"""
        gateway = GovernanceGateway()
        assert gateway.requires_approval(ActionType.DATABASE) is True

    def test_security_requires_approval(self):
        """SECURITY action should always require approval"""
        gateway = GovernanceGateway()
        assert gateway.requires_approval(ActionType.SECURITY) is True

    def test_file_delete_requires_approval(self):
        """FILE_DELETE action should require approval (HIGH risk)"""
        gateway = GovernanceGateway()
        assert gateway.requires_approval(ActionType.FILE_DELETE) is True

    def test_file_modify_no_approval_by_default(self):
        """FILE_MODIFY action should NOT require approval (LOW risk)"""
        gateway = GovernanceGateway()
        assert gateway.requires_approval(ActionType.FILE_MODIFY) is False

    def test_config_change_no_approval_by_default(self):
        """CONFIG_CHANGE action should NOT require approval (MEDIUM risk)"""
        gateway = GovernanceGateway()
        assert gateway.requires_approval(ActionType.CONFIG_CHANGE) is False


class TestProtectedPathDetection:
    """Tests for requires_approval based on protected paths"""

    def test_deploy_path_requires_approval(self):
        """deploy/** paths should require approval"""
        gateway = GovernanceGateway()
        assert (
            gateway.requires_approval(
                ActionType.FILE_MODIFY, ["deploy/kubernetes.yaml"]
            )
            is True
        )

    def test_production_config_requires_approval(self):
        """config/production/** paths should require approval"""
        gateway = GovernanceGateway()
        assert (
            gateway.requires_approval(
                ActionType.FILE_MODIFY, ["config/production/db.yaml"]
            )
            is True
        )

    def test_env_files_require_approval(self):
        """.env* files should require approval"""
        gateway = GovernanceGateway()
        assert gateway.requires_approval(ActionType.FILE_MODIFY, [".env"]) is True
        assert (
            gateway.requires_approval(ActionType.FILE_MODIFY, [".env.production"])
            is True
        )

    def test_secrets_require_approval(self):
        """secrets/** should require approval"""
        gateway = GovernanceGateway()
        assert (
            gateway.requires_approval(ActionType.FILE_MODIFY, ["secrets/api_key.txt"])
            is True
        )

    def test_key_files_require_approval(self):
        """*.key and *.pem files should require approval"""
        gateway = GovernanceGateway()
        assert gateway.requires_approval(ActionType.FILE_MODIFY, ["server.key"]) is True
        assert (
            gateway.requires_approval(ActionType.FILE_MODIFY, ["ssl/cert.pem"]) is True
        )

    def test_normal_files_no_approval(self):
        """Normal source files should NOT require approval"""
        gateway = GovernanceGateway()
        assert (
            gateway.requires_approval(ActionType.FILE_MODIFY, ["src/main.py"]) is False
        )
        assert (
            gateway.requires_approval(ActionType.FILE_MODIFY, ["tests/test_main.py"])
            is False
        )


class TestApprovalWorkflow:
    """Tests for the approval workflow lifecycle"""

    def test_create_approval_request(self):
        """Should create approval request with correct data"""
        gateway = GovernanceGateway()
        request = gateway.create_approval_request(
            action_type=ActionType.DEPLOY,
            description="Deploy to production",
            affected_resources=["prod-server-1", "prod-server-2"],
            rationale="Version 1.0 passed all tests",
        )

        assert request.request_id.startswith("REQ-")
        assert request.action_type == ActionType.DEPLOY
        assert request.risk_level == RiskLevel.CRITICAL
        assert request.description == "Deploy to production"
        assert "prod-server-1" in request.affected_resources
        assert request.approved is None  # Not yet approved

    def test_approve_request(self):
        """Should approve request and move to log"""
        gateway = GovernanceGateway()
        request = gateway.create_approval_request(
            action_type=ActionType.DEPLOY,
            description="Deploy",
            affected_resources=["prod"],
            rationale="Test",
        )

        assert request.request_id in gateway.pending_requests

        result = gateway.approve(request.request_id, "admin@example.com")

        assert result is True
        assert request.request_id not in gateway.pending_requests
        assert len(gateway.approval_log) == 1
        assert gateway.approval_log[0].approved is True
        assert gateway.approval_log[0].approver == "admin@example.com"

    def test_reject_request(self):
        """Should reject request and move to log"""
        gateway = GovernanceGateway()
        request = gateway.create_approval_request(
            action_type=ActionType.DEPLOY,
            description="Deploy",
            affected_resources=["prod"],
            rationale="Test",
        )

        result = gateway.reject(request.request_id, "admin@example.com")

        assert result is True
        assert request.request_id not in gateway.pending_requests
        assert len(gateway.approval_log) == 1
        assert gateway.approval_log[0].approved is False

    def test_approve_nonexistent_request(self):
        """Should return False for non-existent request"""
        gateway = GovernanceGateway()
        result = gateway.approve("REQ-NOTEXIST-0001")
        assert result is False

    def test_get_pending_requests(self):
        """Should return list of pending requests"""
        gateway = GovernanceGateway()
        gateway.create_approval_request(
            action_type=ActionType.DEPLOY,
            description="Deploy 1",
            affected_resources=["prod"],
            rationale="Test",
        )
        gateway.create_approval_request(
            action_type=ActionType.DATABASE,
            description="DB Migration",
            affected_resources=["db"],
            rationale="Test",
        )

        pending = gateway.get_pending_requests()
        assert len(pending) == 2


class TestApprovalCallback:
    """Tests for approval callback functionality"""

    def test_callback_auto_approve(self):
        """Callback that returns True should auto-approve"""
        gateway = GovernanceGateway()
        gateway.set_approval_callback(lambda req: True)

        request = gateway.create_approval_request(
            action_type=ActionType.DEPLOY,
            description="Deploy",
            affected_resources=["prod"],
            rationale="Test",
        )

        result = gateway.wait_for_approval(request)

        assert result is True
        assert len(gateway.approval_log) == 1
        assert gateway.approval_log[0].approved is True

    def test_callback_auto_reject(self):
        """Callback that returns False should auto-reject"""
        gateway = GovernanceGateway()
        gateway.set_approval_callback(lambda req: False)

        request = gateway.create_approval_request(
            action_type=ActionType.DEPLOY,
            description="Deploy",
            affected_resources=["prod"],
            rationale="Test",
        )

        result = gateway.wait_for_approval(request)

        assert result is False
        assert len(gateway.approval_log) == 1
        assert gateway.approval_log[0].approved is False


class TestApprovalRequestSerialization:
    """Tests for ApprovalRequest serialization"""

    def test_to_dict(self):
        """ApprovalRequest.to_dict should return valid dict"""
        request = ApprovalRequest(
            request_id="REQ-20231223-0001",
            action_type=ActionType.DEPLOY,
            risk_level=RiskLevel.CRITICAL,
            description="Deploy",
            affected_resources=["prod"],
            rationale="Test",
        )

        d = request.to_dict()

        assert d["request_id"] == "REQ-20231223-0001"
        assert d["action_type"] == "deploy"
        assert d["risk_level"] == "critical"
        assert "created_at" in d


class TestHighRiskActionsConstant:
    """Tests for HIGH_RISK_ACTIONS constant"""

    def test_critical_actions(self):
        """DEPLOY, DATABASE, SECURITY, FINANCIAL should be CRITICAL"""
        assert HIGH_RISK_ACTIONS[ActionType.DEPLOY] == RiskLevel.CRITICAL
        assert HIGH_RISK_ACTIONS[ActionType.DATABASE] == RiskLevel.CRITICAL
        assert HIGH_RISK_ACTIONS[ActionType.SECURITY] == RiskLevel.CRITICAL
        assert HIGH_RISK_ACTIONS[ActionType.FINANCIAL] == RiskLevel.CRITICAL

    def test_high_risk_actions(self):
        """FILE_DELETE should be HIGH"""
        assert HIGH_RISK_ACTIONS[ActionType.FILE_DELETE] == RiskLevel.HIGH

    def test_medium_risk_actions(self):
        """CONFIG_CHANGE, EXTERNAL_API should be MEDIUM"""
        assert HIGH_RISK_ACTIONS[ActionType.CONFIG_CHANGE] == RiskLevel.MEDIUM
        assert HIGH_RISK_ACTIONS[ActionType.EXTERNAL_API] == RiskLevel.MEDIUM
