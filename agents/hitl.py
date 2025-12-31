"""
HITLGate - Human-in-the-Loop 决策门控
用于高风险操作的人工审批机制。
"""

from dataclasses import dataclass, field
from typing import Dict, Any, Optional
from enum import Enum
import logging
from datetime import datetime

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
    approval_id: Optional[str] = None


class InterruptStatus(Enum):
    """中断状态"""

    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


@dataclass
class InterruptRecord:
    """中断记录"""

    approval_id: str
    action: Dict[str, Any]
    status: InterruptStatus
    state: Optional[Dict[str, Any]] = None
    created_at: datetime = field(default_factory=datetime.now)
    resolved_at: Optional[datetime] = None
    approver: Optional[str] = None
    reason: Optional[str] = None
    resume_payload: Optional[Dict[str, Any]] = None


class HumanInterrupt(Exception):
    """Raised when execution is interrupted for human approval."""

    def __init__(self, record: InterruptRecord):
        self.record = record
        super().__init__(f"HITL interrupt pending: {record.approval_id}")


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
    interrupts: Dict[str, InterruptRecord] = field(default_factory=dict)

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
            approval_id=approval_id,
        )

    def interrupt(
        self,
        action: Dict[str, Any],
        state: Optional[Dict[str, Any]] = None,
    ) -> ApprovalResult:
        """
        请求审批并在需要人工处理时中断执行。

        Returns:
            ApprovalResult if auto-approved, otherwise raises HumanInterrupt.
        """
        result = self.request_approval(action)
        if result.status != ApprovalStatus.PENDING.value:
            return result

        if not result.approval_id:
            raise ValueError("Missing approval_id for pending approval.")

        record = InterruptRecord(
            approval_id=result.approval_id,
            action=action,
            status=InterruptStatus.PENDING,
            state=state,
        )
        self.interrupts[result.approval_id] = record

        interrupt_event = Event(
            type=EventType.INTERRUPT_RAISED,
            source="HITL",
            payload={
                "approval_id": result.approval_id,
                "action": action,
            },
        )
        self.hub.publish(interrupt_event)

        raise HumanInterrupt(record)

    def resume(
        self,
        approval_id: str,
        approved: bool = True,
        approver: str = "human",
        reason: Optional[str] = None,
        resume_payload: Optional[Dict[str, Any]] = None,
    ) -> InterruptRecord:
        """
        恢复中断并记录处理结果。
        """
        record = self.interrupts.get(approval_id)
        if not record:
            raise ValueError(f"Interrupt not found for approval_id: {approval_id}")

        if approved:
            self.approve(approval_id)
            record.status = InterruptStatus.APPROVED
        else:
            self.reject(approval_id, reason=reason or "Rejected by human")
            record.status = InterruptStatus.REJECTED

        record.resolved_at = datetime.now()
        record.approver = approver
        record.reason = reason
        record.resume_payload = resume_payload

        resume_event = Event(
            type=EventType.INTERRUPT_RESUMED,
            source="HITL",
            payload={
                "approval_id": approval_id,
                "approved": approved,
                "approver": approver,
            },
        )
        self.hub.publish(resume_event)

        return record

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
            approval_id=approval_id,
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
            approval_id=approval_id,
        )


__all__ = [
    "HITLGate",
    "ApprovalResult",
    "ApprovalStatus",
    "HumanInterrupt",
    "InterruptRecord",
    "InterruptStatus",
]
