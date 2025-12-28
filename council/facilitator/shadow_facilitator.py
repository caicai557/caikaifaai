"""
Shadow Facilitator - 影子内阁 (投机共识)

实现 2025 Best Practice: Speculative Consensus
使用廉价 Flash 模型预计算共识，仅在分歧时唤醒昂贵 Pro 模型。

Token Savings: 
- 90% cost reduction when Shadow Cabinet achieves unanimous consensus
- ~50% reduction on average (assumes 70% unanimous rate)
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any, Union
from enum import Enum
from datetime import datetime

from council.agents.base_agent import BaseAgent, Vote
from council.protocol.schema import MinimalVote, VoteEnum
from council.facilitator.wald_consensus import WaldConsensus, ConsensusResult, ConsensusDecision


class EscalationReason(Enum):
    """升级原因"""
    DISAGREEMENT = "disagreement"      # 影子内阁有分歧
    LOW_CONFIDENCE = "low_confidence"  # 置信度过低
    CRITICAL_RISK = "critical_risk"    # 检测到关键风险
    TIMEOUT = "timeout"                # 超时


@dataclass
class ShadowResult:
    """影子内阁结果"""
    resolved: bool                          # 是否在影子层解决
    decision: Optional[ConsensusDecision]   # 最终决策
    shadow_votes: List[MinimalVote]         # 影子投票
    escalation_reason: Optional[EscalationReason] = None
    cost_saved_percent: float = 0.0         # 节省成本百分比
    latency_ms: float = 0.0                 # 延迟
    timestamp: datetime = field(default_factory=datetime.now)


class ShadowFacilitator:
    """
    影子内阁促进者
    
    核心逻辑:
    1. 先使用 Flash 模型组成的 "影子内阁" 进行投票
    2. 如果影子内阁达成一致 (全票通过/拒绝)，直接提交
    3. 如果有分歧或低置信度，升级到 Pro 模型 "完整理事会"
    
    Usage:
        shadow = ShadowFacilitator(
            shadow_agents=[Architect("flash"), Coder("flash")],
            pro_agents=[Architect("pro"), Coder("pro")]
        )
        
        result = shadow.deliberate("实现用户登录功能")
        
        if result.resolved:
            print(f"Shadow resolved! Cost saved: {result.cost_saved_percent}%")
        else:
            print(f"Escalated: {result.escalation_reason}")
    """
    
    def __init__(
        self,
        shadow_agents: Optional[List[BaseAgent]] = None,
        pro_agents: Optional[List[BaseAgent]] = None,
        unanimity_required: bool = True,
        min_confidence: float = 0.7,
    ):
        """
        初始化影子促进者
        
        Args:
            shadow_agents: 影子内阁成员 (Flash 模型)
            pro_agents: 完整理事会成员 (Pro 模型)
            unanimity_required: 是否需要全票通过
            min_confidence: 最低置信度阈值
        """
        self.shadow_agents = shadow_agents or []
        self.pro_agents = pro_agents or []
        self.unanimity_required = unanimity_required
        self.min_confidence = min_confidence
        self.wald = WaldConsensus()
        
        # 统计
        self._total_deliberations = 0
        self._shadow_resolved = 0
        self._escalations = 0
        
    def deliberate(self, proposal: str, context: Optional[Dict[str, Any]] = None) -> ShadowResult:
        """
        执行投机共识流程
        
        Args:
            proposal: 提案内容
            context: 可选上下文
            
        Returns:
            ShadowResult: 审议结果
        """
        start_time = datetime.now()
        self._total_deliberations += 1
        
        # Step 1: 影子内阁投票
        shadow_votes = self._collect_shadow_votes(proposal, context)
        
        # Step 2: 检查共识
        escalation_reason = self._check_escalation(shadow_votes)
        
        if escalation_reason is None:
            # 影子层解决
            self._shadow_resolved += 1
            decision = self._determine_decision(shadow_votes)
            
            latency = (datetime.now() - start_time).total_seconds() * 1000
            return ShadowResult(
                resolved=True,
                decision=decision,
                shadow_votes=shadow_votes,
                cost_saved_percent=90.0,  # Flash vs Pro cost ratio
                latency_ms=latency,
            )
        else:
            # 需要升级
            self._escalations += 1
            return self._escalate_to_full_council(
                proposal, context, shadow_votes, escalation_reason, start_time
            )
    
    def _collect_shadow_votes(
        self, 
        proposal: str, 
        context: Optional[Dict[str, Any]]
    ) -> List[MinimalVote]:
        """收集影子内阁投票"""
        votes = []
        
        for agent in self.shadow_agents:
            try:
                # 优先使用结构化方法
                if hasattr(agent, 'vote_structured'):
                    vote = agent.vote_structured(proposal, context)
                else:
                    # 回退到传统方法并转换
                    legacy_vote = agent.vote(proposal, context)
                    vote = self._convert_legacy_vote(legacy_vote)
                votes.append(vote)
            except Exception as e:
                # 容错: 投票失败视为 HOLD
                votes.append(MinimalVote(
                    vote=VoteEnum.HOLD,
                    confidence=0.3,
                    blocking_reason=f"Vote failed: {str(e)[:50]}"
                ))
                
        return votes
    
    def _convert_legacy_vote(self, vote: Vote) -> MinimalVote:
        """转换旧版 Vote 到 MinimalVote"""
        vote_mapping = {
            "approve": VoteEnum.APPROVE,
            "approve_with_changes": VoteEnum.APPROVE_WITH_CHANGES,
            "hold": VoteEnum.HOLD,
            "reject": VoteEnum.REJECT,
        }
        return MinimalVote(
            vote=vote_mapping.get(vote.decision.value, VoteEnum.HOLD),
            confidence=vote.confidence,
            blocking_reason=vote.rationale[:100] if vote.rationale else None,
        )
    
    def _check_escalation(self, votes: List[MinimalVote]) -> Optional[EscalationReason]:
        """检查是否需要升级到完整理事会"""
        if not votes:
            return EscalationReason.TIMEOUT
            
        # 检查一致性
        vote_values = [v.vote for v in votes]
        is_unanimous = len(set(vote_values)) == 1
        
        if self.unanimity_required and not is_unanimous:
            return EscalationReason.DISAGREEMENT
            
        # 检查置信度
        avg_confidence = sum(v.confidence for v in votes) / len(votes)
        if avg_confidence < self.min_confidence:
            return EscalationReason.LOW_CONFIDENCE
            
        # 检查关键风险
        from council.protocol.schema import RiskCategory
        for vote in votes:
            if RiskCategory.SECURITY in vote.risks:
                # 安全风险总是升级
                return EscalationReason.CRITICAL_RISK
                
        return None  # 无需升级
    
    def _determine_decision(self, votes: List[MinimalVote]) -> ConsensusDecision:
        """根据投票确定决策"""
        if not votes:
            return ConsensusDecision.HOLD_FOR_HUMAN
            
        # 全票通过
        all_approve = all(v.vote in [VoteEnum.APPROVE, VoteEnum.APPROVE_WITH_CHANGES] for v in votes)
        if all_approve:
            return ConsensusDecision.AUTO_COMMIT
            
        # 全票拒绝
        all_reject = all(v.vote == VoteEnum.REJECT for v in votes)
        if all_reject:
            return ConsensusDecision.REJECT
            
        return ConsensusDecision.HOLD_FOR_HUMAN
    
    def _escalate_to_full_council(
        self,
        proposal: str,
        context: Optional[Dict[str, Any]],
        shadow_votes: List[MinimalVote],
        reason: EscalationReason,
        start_time: datetime,
    ) -> ShadowResult:
        """升级到完整理事会"""
        # 将影子投票作为上下文提供给 Pro 模型
        shadow_summary = self._summarize_shadow_votes(shadow_votes)
        enhanced_context = {
            **(context or {}),
            "shadow_cabinet_summary": shadow_summary,
            "escalation_reason": reason.value,
        }
        
        # 收集 Pro 模型投票
        pro_votes = []
        for agent in self.pro_agents:
            try:
                if hasattr(agent, 'vote_structured'):
                    vote = agent.vote_structured(proposal, enhanced_context)
                else:
                    legacy_vote = agent.vote(proposal, enhanced_context)
                    vote = self._convert_legacy_vote(legacy_vote)
                pro_votes.append(vote)
            except Exception:
                pro_votes.append(MinimalVote(vote=VoteEnum.HOLD, confidence=0.3))
        
        # 使用 Wald 算法评估
        all_votes = shadow_votes + pro_votes
        vote_dicts = [
            {"decision": v.vote.to_legacy(), "confidence": v.confidence, "agent": f"agent_{i}"}
            for i, v in enumerate(all_votes)
        ]
        wald_result = self.wald.evaluate(vote_dicts)
        
        latency = (datetime.now() - start_time).total_seconds() * 1000
        
        return ShadowResult(
            resolved=False,
            decision=wald_result.decision,
            shadow_votes=shadow_votes,
            escalation_reason=reason,
            cost_saved_percent=0.0,  # No savings on escalation
            latency_ms=latency,
        )
    
    def _summarize_shadow_votes(self, votes: List[MinimalVote]) -> str:
        """生成影子投票摘要"""
        approve_count = sum(1 for v in votes if v.vote in [VoteEnum.APPROVE, VoteEnum.APPROVE_WITH_CHANGES])
        reject_count = sum(1 for v in votes if v.vote == VoteEnum.REJECT)
        hold_count = len(votes) - approve_count - reject_count
        
        concerns = [v.blocking_reason for v in votes if v.blocking_reason]
        
        return f"Shadow Cabinet: {approve_count} approve, {reject_count} reject, {hold_count} hold. Concerns: {concerns[:3]}"
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        resolution_rate = (
            self._shadow_resolved / self._total_deliberations * 100
            if self._total_deliberations > 0 else 0
        )
        estimated_savings = resolution_rate * 0.9  # 90% per resolved
        
        return {
            "total_deliberations": self._total_deliberations,
            "shadow_resolved": self._shadow_resolved,
            "escalations": self._escalations,
            "resolution_rate_percent": round(resolution_rate, 1),
            "estimated_cost_savings_percent": round(estimated_savings, 1),
        }


# 导出
__all__ = [
    "ShadowFacilitator",
    "ShadowResult",
    "EscalationReason",
]
