"""
Governance Gateway - HITL 关键动作网关
实现人在回路 (Human-in-the-Loop) 治理机制
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Callable
from enum import Enum
from datetime import datetime
import json
import re


class RiskLevel(Enum):
    """风险级别"""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ActionType(Enum):
    """动作类型"""

    FILE_DELETE = "file_delete"
    FILE_MODIFY = "file_modify"
    CONFIG_CHANGE = "config_change"
    DEPLOY = "deploy"
    DATABASE = "database"
    EXTERNAL_API = "external_api"
    SECURITY = "security"
    FINANCIAL = "financial"


@dataclass
class ApprovalRequest:
    """审批请求"""

    request_id: str
    action_type: ActionType
    risk_level: RiskLevel
    description: str
    affected_resources: List[str]
    rationale: str
    council_decision: Optional[Dict[str, Any]] = None
    requestor: str = "system"
    created_at: datetime = field(default_factory=datetime.now)
    approved: Optional[bool] = None
    approver: Optional[str] = None
    approved_at: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "request_id": self.request_id,
            "action_type": self.action_type.value,
            "risk_level": self.risk_level.value,
            "description": self.description,
            "affected_resources": self.affected_resources,
            "rationale": self.rationale,
            "council_decision": self.council_decision,
            "requestor": self.requestor,
            "created_at": self.created_at.isoformat(),
            "approved": self.approved,
            "approver": self.approver,
            "approved_at": self.approved_at.isoformat() if self.approved_at else None,
        }


# 高风险动作定义
HIGH_RISK_ACTIONS = {
    ActionType.FILE_DELETE: RiskLevel.HIGH,
    ActionType.DEPLOY: RiskLevel.CRITICAL,
    ActionType.DATABASE: RiskLevel.CRITICAL,
    ActionType.SECURITY: RiskLevel.CRITICAL,
    ActionType.FINANCIAL: RiskLevel.CRITICAL,
    ActionType.CONFIG_CHANGE: RiskLevel.MEDIUM,
    ActionType.EXTERNAL_API: RiskLevel.MEDIUM,
    ActionType.FILE_MODIFY: RiskLevel.LOW,
}

# 危险内容模式 (Regex)
DANGEROUS_PATTERNS = [
    (r"rm\s+-[rf]{1,2}", RiskLevel.CRITICAL),  # rm -rf
    (r"mkfs", RiskLevel.CRITICAL),  # 格式化
    (r"dd\s+if=", RiskLevel.CRITICAL),  # dd 命令
    (r"os\.system\(['\"]rm", RiskLevel.CRITICAL),  # os.system('rm...')
    (r"subprocess\.call\(['\"]rm", RiskLevel.CRITICAL),  # subprocess rm
    (r"eval\(", RiskLevel.HIGH),  # eval() - 高危但不一定致命
    (r"exec\(", RiskLevel.HIGH),  # exec()
    (r"__import__", RiskLevel.HIGH),  # 动态导入
]

# 需要强制人工审批的路径模式
PROTECTED_PATHS = [
    "deploy/**",
    "config/production/**",
    ".env*",
    "secrets/**",
    "database/migrations/**",
    "*.key",
    "*.pem",
]


class GovernanceGateway:
    """
    HITL 治理网关

    核心功能:
    1. 拦截高风险操作
    2. 生成审批请求
    3. 等待人工确认
    4. 记录审批日志

    使用示例:
        gateway = GovernanceGateway()

        # 检查操作是否需要审批
        if gateway.requires_approval(ActionType.DEPLOY, ["production"]):
            request = gateway.create_approval_request(
                action_type=ActionType.DEPLOY,
                description="部署到生产环境",
                affected_resources=["production-server"],
                rationale="版本 v1.2.0 已通过所有测试",
            )

            # 等待审批
            if gateway.wait_for_approval(request):
                # 执行操作
                pass
    """

    def __init__(self):
        self.pending_requests: Dict[str, ApprovalRequest] = {}
        self.approval_log: List[ApprovalRequest] = []
        self._request_counter = 0
        self._approval_callback: Optional[Callable[[ApprovalRequest], bool]] = None

<<<<<<< HEAD
    def set_approval_callback(self, callback: Callable[[ApprovalRequest], bool]) -> None:
=======
    def set_approval_callback(
        self, callback: Callable[[ApprovalRequest], bool]
    ) -> None:
>>>>>>> e2df45bcf4fae044c2ec81c7ea50a183bdc8bd86
        """
        设置审批回调函数

        Args:
            callback: 审批回调，接收 ApprovalRequest，返回是否批准
        """
        self._approval_callback = callback

    def _scan_content(self, content: str) -> RiskLevel:
        """
        扫描内容中的危险模式

        Args:
            content: 文件内容或命令字符串

        Returns:
            检测到的最高风险等级
        """
        max_risk = RiskLevel.LOW

        for pattern, risk in DANGEROUS_PATTERNS:
            if re.search(pattern, content):
                # 升级风险
                if risk == RiskLevel.CRITICAL:
                    return RiskLevel.CRITICAL
                if risk == RiskLevel.HIGH and max_risk != RiskLevel.CRITICAL:
                    max_risk = RiskLevel.HIGH
                elif risk == RiskLevel.MEDIUM and max_risk == RiskLevel.LOW:
                    max_risk = RiskLevel.MEDIUM

        return max_risk

    def requires_approval(
        self,
        action_type: ActionType,
        affected_paths: Optional[List[str]] = None,
        content: Optional[str] = None,
    ) -> bool:
        """
        检查操作是否需要人工审批

        Args:
            action_type: 动作类型
            affected_paths: 受影响的路径列表
            content: 涉及的内容（如有）

        Returns:
            是否需要审批
        """
        # 1. 检查动作类型基础风险
        base_risk = HIGH_RISK_ACTIONS.get(action_type, RiskLevel.LOW)
        if base_risk in [RiskLevel.HIGH, RiskLevel.CRITICAL]:
            return True

        # 2. 检查内容风险 (Deep Inspection)
        if content:
            content_risk = self._scan_content(content)
            if content_risk in [RiskLevel.HIGH, RiskLevel.CRITICAL]:
                return True

        # 3. 检查受保护路径
        if affected_paths:
            import fnmatch

            for path in affected_paths:
                for pattern in PROTECTED_PATHS:
                    if fnmatch.fnmatch(path, pattern):
                        return True

        return False

<<<<<<< HEAD
    def auto_approve_with_council(self, request: ApprovalRequest, consensus_result: Dict[str, Any]) -> bool:
=======
    def auto_approve_with_council(
        self, request: ApprovalRequest, consensus_result: Dict[str, Any]
    ) -> bool:
>>>>>>> e2df45bcf4fae044c2ec81c7ea50a183bdc8bd86
        """
        尝试使用 Council 共识自动批准

        只有当 Council 共识极高 (AUTO_COMMIT) 且风险不是 CRITICAL 时才允许。
        CRITICAL 风险永远需要人工。

        Args:
            request: 审批请求
            consensus_result: Council 共识结果 (ConsensusResult 对象或字典)

        Returns:
            是否自动批准成功
        """
        # 永远不自动批准 CRITICAL
        if request.risk_level == RiskLevel.CRITICAL:
            return False

        # 获取某些属性，兼顾对象和字典
        decision = getattr(consensus_result, "decision", None)
        if not decision and isinstance(consensus_result, dict):
            decision = consensus_result.get("decision")

        # 必须是 AUTO_COMMIT
        # 注意：这里假设 consensus_result.decision 是 Enum 或对应的字符串值
        # 为兼容性，转换字符串比较
<<<<<<< HEAD
        decision_str = str(decision.value) if hasattr(decision, "value") else str(decision)
=======
        decision_str = (
            str(decision.value) if hasattr(decision, "value") else str(decision)
        )
>>>>>>> e2df45bcf4fae044c2ec81c7ea50a183bdc8bd86

        if decision_str == "auto_commit":
            return self.approve(request.request_id, "council_auto_commit")

        return False

    def create_approval_request(
        self,
        action_type: ActionType,
        description: str,
        affected_resources: List[str],
        rationale: str,
        council_decision: Optional[Dict[str, Any]] = None,
        requestor: str = "system",
    ) -> ApprovalRequest:
        """
        创建审批请求

        Args:
            action_type: 动作类型
            description: 操作描述
            affected_resources: 受影响的资源
            rationale: 理由说明
            council_decision: 理事会决策（如有）
            requestor: 请求者

        Returns:
            审批请求对象
        """
        self._request_counter += 1
<<<<<<< HEAD
        request_id = f"REQ-{datetime.now().strftime('%Y%m%d')}-{self._request_counter:04d}"
=======
        request_id = (
            f"REQ-{datetime.now().strftime('%Y%m%d')}-{self._request_counter:04d}"
        )
>>>>>>> e2df45bcf4fae044c2ec81c7ea50a183bdc8bd86

        # 重新计算风险（因为可能没传入 content，这里只能基于 action_type 和资源估算）
        # 理想情况下调用者应该先检测风险再创建请求，或者这里只做记录
        risk_level = HIGH_RISK_ACTIONS.get(action_type, RiskLevel.LOW)

        request = ApprovalRequest(
            request_id=request_id,
            action_type=action_type,
            risk_level=risk_level,
            description=description,
            affected_resources=affected_resources,
            rationale=rationale,
            council_decision=council_decision,
            requestor=requestor,
        )

        self.pending_requests[request_id] = request
        return request

    def approve(self, request_id: str, approver: str = "human") -> bool:
        """
        批准请求

        Args:
            request_id: 请求ID
            approver: 批准者

        Returns:
            是否成功
        """
        if request_id not in self.pending_requests:
            return False

        request = self.pending_requests.pop(request_id)
        request.approved = True
        request.approver = approver
        request.approved_at = datetime.now()

        self.approval_log.append(request)
        return True

    def reject(self, request_id: str, approver: str = "human") -> bool:
        """
        拒绝请求

        Args:
            request_id: 请求ID
            approver: 拒绝者

        Returns:
            是否成功
        """
        if request_id not in self.pending_requests:
            return False

        request = self.pending_requests.pop(request_id)
        request.approved = False
        request.approver = approver
        request.approved_at = datetime.now()

        self.approval_log.append(request)
        return True

<<<<<<< HEAD
    def wait_for_approval(self, request: ApprovalRequest, timeout_seconds: int = 300) -> bool:
=======
    def wait_for_approval(
        self, request: ApprovalRequest, timeout_seconds: int = 300
    ) -> bool:
>>>>>>> e2df45bcf4fae044c2ec81c7ea50a183bdc8bd86
        """
        等待人工审批（同步版本）

        Args:
            request: 审批请求
            timeout_seconds: 超时秒数

        Returns:
            是否被批准
        """
        # 如果设置了回调，使用回调
        if self._approval_callback:
            result = self._approval_callback(request)
            if result:
                self.approve(request.request_id, "callback")
            else:
                self.reject(request.request_id, "callback")
            return result

        # 否则打印请求并返回 False（需要外部处理）
        print(f"\n{'=' * 60}")
        print(f"⚠️  审批请求: {request.request_id}")
        print(f"{'=' * 60}")
        print(f"类型: {request.action_type.value}")
        print(f"风险: {request.risk_level.value}")
        print(f"描述: {request.description}")
        print(f"资源: {', '.join(request.affected_resources)}")
        print(f"理由: {request.rationale}")
        if request.council_decision:
            print(
                f"理事会决策: {json.dumps(request.council_decision, ensure_ascii=False, indent=2)}"
            )
        print(f"{'=' * 60}")
        print("请使用 gateway.approve() 或 gateway.reject() 处理此请求")

        return False

    def get_pending_requests(self) -> List[ApprovalRequest]:
        """获取所有待处理请求"""
        return list(self.pending_requests.values())

    def get_approval_log(self, limit: int = 10) -> List[Dict[str, Any]]:
        """获取审批日志"""
        return [r.to_dict() for r in self.approval_log[-limit:]]


# 导出
__all__ = [
    "GovernanceGateway",
    "ApprovalRequest",
    "ActionType",
    "RiskLevel",
    "HIGH_RISK_ACTIONS",
    "PROTECTED_PATHS",
]
