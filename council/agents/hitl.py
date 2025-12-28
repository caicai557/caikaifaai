"""
HITLGate - Human-in-the-Loop 决策门控
用于高风险操作的人工审批机制。
"""

from dataclasses import dataclass, field
from typing import Dict, Any, Optional
from enum import Enum
import logging

from council.orchestration.hub import Hub
from council.orchestration.events import Event, EventType


class ApprovalStatus(Enum):
    """审批状态"""

    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    AUTO_APPROVED = "AUTO_APPROVED"


@dataclass
class ApprovalResult:
    """审批结果"""

    status: str
    approved: bool
    reason: Optional[str] = None
    action: Optional[Dict[str, Any]] = None


@dataclass
class HITLGate:
    """
    Human-in-the-Loop 门控

    职责:
    - 拦截高风险操作
    - 请求人工审批
    - 自动批准低风险操作 (可配置)
    """

    hub: Hub
    auto_approve_low_risk: bool = False
    pending_approvals: Dict[str, Dict[str, Any]] = field(default_factory=dict)

    def __post_init__(self):
        self.logger = logging.getLogger("HITL")

    def request_approval(self, action: Dict[str, Any]) -> ApprovalResult:
        """
        请求操作审批

        Args:
            action: 待审批的操作
                - type: 操作类型 (如 DELETE_FILE, DEPLOY)
                - target: 操作目标
                - risk: 风险级别 (low, medium, high)

        Returns:
            ApprovalResult: 审批结果
        """
        risk = action.get("risk", "medium")
        action_type = action.get("type", "UNKNOWN")
        target = action.get("target", "unknown")

        self.logger.info(f"HITL: Approval requested for {action_type} on {target}")

        # 低风险自动批准
        if risk == "low" and self.auto_approve_low_risk:
            self.logger.info(f"HITL: Auto-approved low-risk action: {action_type}")
            return ApprovalResult(
                status=ApprovalStatus.AUTO_APPROVED.value,
                approved=True,
                reason="Auto-approved: low risk",
                action=action,
            )

        # 高风险需要人工审批
        import uuid

        approval_id = str(uuid.uuid4())
        self.pending_approvals[approval_id] = action

        # 发布审批请求事件
        approval_event = Event(
            type=EventType.QUERY_RAISED,  # 使用现有事件类型
            source="HITL",
            payload={
                "approval_id": approval_id,
                "action": action,
                "message": f"[HITL] 请审批操作: {action_type} on {target}",
            },
        )
        self.hub.publish(approval_event)

        self.logger.warning(
            f"HITL: Pending approval for {action_type} (ID: {approval_id})"
        )

        return ApprovalResult(
            status=ApprovalStatus.PENDING.value,
            approved=False,
            reason=f"Pending human approval (ID: {approval_id})",
            action=action,
        )

    def approve(self, approval_id: str) -> ApprovalResult:
        """
        批准待处理的操作

        Args:
            approval_id: 审批 ID

        Returns:
            ApprovalResult: 审批结果
        """
        if approval_id not in self.pending_approvals:
            return ApprovalResult(
                status="ERROR",
                approved=False,
                reason=f"Approval ID not found: {approval_id}",
            )

        action = self.pending_approvals.pop(approval_id)
        self.logger.info(f"HITL: Approved action: {action.get('type')}")

        return ApprovalResult(
            status=ApprovalStatus.APPROVED.value,
            approved=True,
            reason="Human approved",
            action=action,
        )

    def reject(
        self, approval_id: str, reason: str = "Rejected by human"
    ) -> ApprovalResult:
        """
        拒绝待处理的操作

        Args:
            approval_id: 审批 ID
            reason: 拒绝原因

        Returns:
            ApprovalResult: 审批结果
        """
        if approval_id not in self.pending_approvals:
            return ApprovalResult(
                status="ERROR",
                approved=False,
                reason=f"Approval ID not found: {approval_id}",
            )

        action = self.pending_approvals.pop(approval_id)
        self.logger.warning(f"HITL: Rejected action: {action.get('type')} - {reason}")

        return ApprovalResult(
            status=ApprovalStatus.REJECTED.value,
            approved=False,
            reason=reason,
            action=action,
        )


__all__ = ["HITLGate", "ApprovalResult", "ApprovalStatus"]
