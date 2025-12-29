"""
Adaptive Router - 自适应混合协议路由器

实现 2025 AGI 编排层最佳实践中的自适应混合协议。

核心功能:
- 风险评估: assess_risk(task) → low/medium/high/critical
- 路由决策: 单模型响应 vs 全理事会审议
"""

from dataclasses import dataclass
from typing import List, Optional
from enum import Enum
import re

from council.orchestration.blast_radius import BlastRadiusAnalyzer, ImpactLevel


class RiskLevel(Enum):
    """风险级别"""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ResponseMode(Enum):
    """响应模式"""

    SINGLE_MODEL = "single_model"  # 单模型快速响应
    SWARM_VERIFY = "swarm_verify"  # Swarm + Wald 验证
    FULL_COUNCIL = "full_council"  # 全理事会审议


@dataclass
class RoutingDecision:
    """路由决策结果"""

    mode: ResponseMode
    risk_level: RiskLevel
    reason: str
    required_approvers: List[str]


# 高风险关键词
HIGH_RISK_KEYWORDS = [
    r"\bgit\s+push\b",
    r"\bdeploy\b",
    r"\bproduction\b",
    r"\bdelete\b",
    r"\bdrop\s+table\b",
    r"\brm\s+-rf\b",
    r"\b\.env\b",
    r"\bsecret\b",
    r"\bapi[_-]?key\b",
    r"\bpassword\b",
    r"\btoken\b",
    r"\bcredential\b",
    r"\bdatabase\b",
    r"\bmigration\b",
]

# 中等风险关键词
MEDIUM_RISK_KEYWORDS = [
    r"\brefactor\b",
    r"\bmerge\b",
    r"\brewrite\b",
    r"\bbreaking\s+change\b",
    r"\bapi\b",
    r"\bschema\b",
    r"\bconfig\b",
    r"\bauth\b",
    r"\blogin\b",
    r"\bpayment\b",
]

# 低风险关键词
LOW_RISK_KEYWORDS = [
    r"\btypo\b",
    r"\bfix\s+lint\b",
    r"\bformat\b",
    r"\bcomment\b",
    r"\bdoc\b",
    r"\breadme\b",
    r"\btest\b",
]


class AdaptiveRouter:
    """
    自适应混合协议路由器

    Usage:
        router = AdaptiveRouter()
        decision = router.route("实现用户登录功能")

        if decision.mode == ResponseMode.SINGLE_MODEL:
            # 快速单模型响应
            pass
        elif decision.mode == ResponseMode.FULL_COUNCIL:
            # 全理事会审议
            pass
    """

    def __init__(self, project_root: str = "."):
        self._high_patterns = [re.compile(p, re.IGNORECASE) for p in HIGH_RISK_KEYWORDS]
        self._medium_patterns = [
            re.compile(p, re.IGNORECASE) for p in MEDIUM_RISK_KEYWORDS
        ]
        self._low_patterns = [re.compile(p, re.IGNORECASE) for p in LOW_RISK_KEYWORDS]

        # 2025 Best Practice: Impact-Aware Routing
        self._blast_analyzer = BlastRadiusAnalyzer(project_root)

    def assess_risk(
        self,
        task: str,
        context: Optional[str] = None,
        affected_files: Optional[List[str]] = None,
    ) -> RiskLevel:
        """
        评估任务风险级别 (含代码影响分析)

        Args:
            task: 任务描述
            context: 额外上下文
            affected_files: 受影响的文件列表 (可选，用于 Blast Radius 分析)

        Returns:
            RiskLevel
        """
        text = f"{task} {context or ''}"

        # Step 1: 基于关键词的风险评估
        keyword_risk = RiskLevel.MEDIUM

        for pattern in self._high_patterns:
            if pattern.search(text):
                keyword_risk = RiskLevel.HIGH
                break
        else:
            for pattern in self._medium_patterns:
                if pattern.search(text):
                    keyword_risk = RiskLevel.MEDIUM
                    break
            else:
                for pattern in self._low_patterns:
                    if pattern.search(text):
                        keyword_risk = RiskLevel.LOW
                        break

        # Step 2: Blast Radius 分析 (如果提供了文件列表)
        if affected_files:
            blast_result = self._blast_analyzer.analyze_multiple(affected_files)

            # 影响级别映射到风险级别
            impact_risk_map = {
                ImpactLevel.LEAF: RiskLevel.LOW,
                ImpactLevel.LOW: RiskLevel.LOW,
                ImpactLevel.MEDIUM: RiskLevel.MEDIUM,
                ImpactLevel.HIGH: RiskLevel.HIGH,
                ImpactLevel.CORE: RiskLevel.CRITICAL,
            }
            blast_risk = impact_risk_map.get(blast_result.impact_level, RiskLevel.MEDIUM)

            # 取两者中更高的风险级别
            risk_order = [RiskLevel.LOW, RiskLevel.MEDIUM, RiskLevel.HIGH, RiskLevel.CRITICAL]
            keyword_idx = risk_order.index(keyword_risk) if keyword_risk in risk_order else 1
            blast_idx = risk_order.index(blast_risk) if blast_risk in risk_order else 1

            return risk_order[max(keyword_idx, blast_idx)]

        return keyword_risk

    def route(self, task: str, context: Optional[str] = None) -> RoutingDecision:
        """
        路由决策

        Args:
            task: 任务描述
            context: 额外上下文

        Returns:
            RoutingDecision
        """
        risk = self.assess_risk(task, context)

        if risk == RiskLevel.LOW:
            return RoutingDecision(
                mode=ResponseMode.SINGLE_MODEL,
                risk_level=risk,
                reason="低风险任务，使用单模型快速响应",
                required_approvers=[],
            )

        elif risk == RiskLevel.MEDIUM:
            return RoutingDecision(
                mode=ResponseMode.SWARM_VERIFY,
                risk_level=risk,
                reason="中等风险任务，使用 Swarm + Wald 验证",
                required_approvers=["wald_score"],
            )

        elif risk == RiskLevel.HIGH:
            return RoutingDecision(
                mode=ResponseMode.FULL_COUNCIL,
                risk_level=risk,
                reason="高风险任务，需要全理事会审议",
                required_approvers=["wald_score", "codex_review"],
            )

        else:  # CRITICAL
            return RoutingDecision(
                mode=ResponseMode.FULL_COUNCIL,
                risk_level=risk,
                reason="关键任务，需要全理事会审议 + 人工确认",
                required_approvers=["wald_score", "codex_review", "human"],
            )

    def explain_decision(self, decision: RoutingDecision) -> str:
        """
        解释路由决策

        Args:
            decision: 路由决策

        Returns:
            解释文本
        """
        lines = [
            "=== ROUTING DECISION ===",
            f"Risk Level: {decision.risk_level.value.upper()}",
            f"Response Mode: {decision.mode.value}",
            f"Reason: {decision.reason}",
        ]

        if decision.required_approvers:
            lines.append(
                f"Required Approvers: {', '.join(decision.required_approvers)}"
            )

        return "\n".join(lines)


# 导出
__all__ = [
    "AdaptiveRouter",
    "RoutingDecision",
    "RiskLevel",
    "ResponseMode",
]
