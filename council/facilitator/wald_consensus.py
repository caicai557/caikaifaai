"""
Wald Consensus - Wald 序列分析共识算法
实现 Sequential Probability Ratio Test (SPRT) 用于理事会共识决策
"""

from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from enum import Enum
import math


class ConsensusDecision(Enum):
    """共识决策结果"""
    AUTO_COMMIT = "auto_commit"      # 自动提交
    HOLD_FOR_HUMAN = "hold_for_human"  # 等待人工审核
    REJECT = "reject"                # 拒绝


@dataclass
class WaldConfig:
    """Wald 算法配置"""
    upper_limit: float = 0.95   # π 达到此值则自动提交
    lower_limit: float = 0.30   # π 低于此值则拒绝
    prior_approve: float = 0.70  # 批准的先验概率

    def __post_init__(self):
        assert 0 < self.lower_limit < self.upper_limit < 1
        assert 0 < self.prior_approve < 1


@dataclass
class ConsensusResult:
    """共识计算结果"""
    decision: ConsensusDecision
    pi_approve: float  # 批准的后验概率
    pi_reject: float   # 拒绝的后验概率
    likelihood_ratio: float  # 似然比
    votes_summary: List[Dict[str, Any]]
    reason: str
    iteration: int = 1


class WaldConsensus:
    """
    Wald 序列分析共识检测器

    基于 Sequential Probability Ratio Test (SPRT) 实现：
    - 实时评估理事会达成共识的概率
    - 一旦概率达标即终止会议，节省 Token

    算法:
        似然比 L = Π [P(vote_i | H_approve) / P(vote_i | H_reject)]
        后验概率 π = (prior * L) / (prior * L + (1 - prior))

        决策规则:
          if π ≥ upper_limit: auto_commit()
          elif π ≤ lower_limit: reject()
          else: continue_or_human_review()

    使用示例:
        detector = WaldConsensus()
        result = detector.evaluate(votes)
        if result.decision == ConsensusDecision.AUTO_COMMIT:
            # 自动提交
            pass
    """

    def __init__(self, config: Optional[WaldConfig] = None):
        self.config = config or WaldConfig()

    def _vote_likelihood(self, confidence: float, is_approve: bool) -> tuple:
        """
        计算投票的似然值

        Args:
            confidence: 投票置信度 (0-1)
            is_approve: 是否为批准投票

        Returns:
            (P(vote|approve), P(vote|reject))
        """
        if is_approve:
            # 批准投票：置信度越高，在批准假设下越可能
            p_approve = confidence
            p_reject = 1 - confidence
        else:
            # 拒绝/hold 投票：置信度越高，在拒绝假设下越可能
            p_approve = 1 - confidence
            p_reject = confidence

        # 避免除零
        p_approve = max(p_approve, 0.01)
        p_reject = max(p_reject, 0.01)

        return p_approve, p_reject

    def evaluate(self, votes: List[Dict[str, Any]]) -> ConsensusResult:
        """
        评估投票并计算共识

        Args:
            votes: 投票列表，每个投票应包含:
                   - agent: 智能体名称
                   - decision: "approve" | "approve_with_changes" | "hold" | "reject"
                   - confidence: 0.0 - 1.0
                   - rationale: 理由

        Returns:
            ConsensusResult: 共识结果
        """
        if not votes:
            return ConsensusResult(
                decision=ConsensusDecision.HOLD_FOR_HUMAN,
                pi_approve=0.5,
                pi_reject=0.5,
                likelihood_ratio=1.0,
                votes_summary=[],
                reason="没有收到任何投票",
            )

        # 计算似然比
        log_likelihood = 0.0
        votes_summary = []

        for vote in votes:
            decision = vote.get("decision", "hold")
            confidence = vote.get("confidence", 0.5)

            # 判断是否为批准投票
            is_approve = decision in ["approve", "approve_with_changes"]

            p_approve, p_reject = self._vote_likelihood(confidence, is_approve)
            log_likelihood += math.log(p_approve / p_reject)

            votes_summary.append({
                "agent": vote.get("agent", "Unknown"),
                "decision": decision,
                "confidence": confidence,
                "p_approve": p_approve,
                "p_reject": p_reject,
            })

        # 计算似然比 L
        likelihood_ratio = math.exp(log_likelihood)

        # 计算后验概率
        prior = self.config.prior_approve
        pi_approve = (prior * likelihood_ratio) / (
            prior * likelihood_ratio + (1 - prior)
        )
        pi_reject = 1 - pi_approve

        # 决策
        if pi_approve >= self.config.upper_limit:
            decision = ConsensusDecision.AUTO_COMMIT
            reason = f"共识概率 π={pi_approve:.3f} ≥ {self.config.upper_limit}，自动提交"
        elif pi_approve <= self.config.lower_limit:
            decision = ConsensusDecision.REJECT
            reason = f"共识概率 π={pi_approve:.3f} ≤ {self.config.lower_limit}，拒绝提案"
        else:
            decision = ConsensusDecision.HOLD_FOR_HUMAN
            reason = f"共识概率 π={pi_approve:.3f} 处于不确定区间，需人工审核"

        return ConsensusResult(
            decision=decision,
            pi_approve=pi_approve,
            pi_reject=pi_reject,
            likelihood_ratio=likelihood_ratio,
            votes_summary=votes_summary,
            reason=reason,
        )

    def should_continue(self, result: ConsensusResult, max_iterations: int = 5) -> bool:
        """
        检查是否应该继续迭代

        Args:
            result: 当前共识结果
            max_iterations: 最大迭代次数

        Returns:
            是否应该继续
        """
        if result.iteration >= max_iterations:
            return False

        if result.decision in [ConsensusDecision.AUTO_COMMIT, ConsensusDecision.REJECT]:
            return False

        return True

    def get_semantic_entropy(self, votes: List[Dict[str, Any]]) -> float:
        """
        计算语义熵 - 衡量投票的不确定性

        熵越低表示共识越强，熵为0表示完全一致

        Args:
            votes: 投票列表

        Returns:
            语义熵值 (0-1)
        """
        if not votes:
            return 1.0  # 最大不确定性

        # 统计各决策类型
        decision_counts = {}
        for vote in votes:
            d = vote.get("decision", "hold")
            decision_counts[d] = decision_counts.get(d, 0) + 1

        # 计算熵
        total = len(votes)
        entropy = 0.0
        for count in decision_counts.values():
            if count > 0:
                p = count / total
                entropy -= p * math.log2(p)

        # 归一化到 0-1 (假设最多4种决策类型)
        max_entropy = math.log2(4)
        normalized_entropy = entropy / max_entropy if max_entropy > 0 else 0

        return normalized_entropy


# 导出
__all__ = [
    "WaldConsensus",
    "WaldConfig",
    "ConsensusResult",
    "ConsensusDecision",
]
