"""
Tests for Shadow Facilitator

验证投机共识 (Speculative Consensus) 逻辑。
"""

import unittest
from unittest.mock import MagicMock
import sys
import os

sys.path.append(os.getcwd())

from council.facilitator.shadow_facilitator import (
    ShadowFacilitator,
    ShadowResult,
    EscalationReason,
)
from council.protocol.schema import MinimalVote, VoteEnum, RiskCategory
from council.facilitator.wald_consensus import ConsensusDecision


class TestShadowFacilitator(unittest.TestCase):

    def _create_mock_agent(self, vote_result: MinimalVote):
        """创建返回指定投票的 mock agent"""
        agent = MagicMock()
        agent.vote_structured = MagicMock(return_value=vote_result)
        return agent

    def test_unanimous_approve_resolves_in_shadow(self):
        """全票通过应在影子层解决"""
        shadow_agents = [
            self._create_mock_agent(MinimalVote(vote=VoteEnum.APPROVE, confidence=0.9)),
            self._create_mock_agent(MinimalVote(vote=VoteEnum.APPROVE, confidence=0.85)),
        ]

        facilitator = ShadowFacilitator(shadow_agents=shadow_agents)
        result = facilitator.deliberate("Add logging")

        self.assertTrue(result.resolved)
        self.assertEqual(result.decision, ConsensusDecision.AUTO_COMMIT)
        self.assertEqual(result.cost_saved_percent, 90.0)
        self.assertIsNone(result.escalation_reason)

    def test_unanimous_reject_resolves_in_shadow(self):
        """全票拒绝应在影子层解决"""
        shadow_agents = [
            self._create_mock_agent(MinimalVote(vote=VoteEnum.REJECT, confidence=0.9)),
            self._create_mock_agent(MinimalVote(vote=VoteEnum.REJECT, confidence=0.8)),
        ]

        facilitator = ShadowFacilitator(shadow_agents=shadow_agents)
        result = facilitator.deliberate("Remove auth")

        self.assertTrue(result.resolved)
        self.assertEqual(result.decision, ConsensusDecision.REJECT)

    def test_disagreement_triggers_escalation(self):
        """分歧应触发升级"""
        shadow_agents = [
            self._create_mock_agent(MinimalVote(vote=VoteEnum.APPROVE, confidence=0.9)),
            self._create_mock_agent(MinimalVote(vote=VoteEnum.REJECT, confidence=0.8)),
        ]
        pro_agents = [
            self._create_mock_agent(MinimalVote(vote=VoteEnum.APPROVE, confidence=0.95)),
        ]

        facilitator = ShadowFacilitator(
            shadow_agents=shadow_agents,
            pro_agents=pro_agents,
        )
        result = facilitator.deliberate("Refactor core")

        self.assertFalse(result.resolved)
        self.assertEqual(result.escalation_reason, EscalationReason.DISAGREEMENT)
        self.assertEqual(result.cost_saved_percent, 0.0)

    def test_low_confidence_triggers_escalation(self):
        """低置信度应触发升级"""
        shadow_agents = [
            self._create_mock_agent(MinimalVote(vote=VoteEnum.APPROVE, confidence=0.5)),
            self._create_mock_agent(MinimalVote(vote=VoteEnum.APPROVE, confidence=0.4)),
        ]

        facilitator = ShadowFacilitator(
            shadow_agents=shadow_agents,
            min_confidence=0.7,
        )
        result = facilitator.deliberate("Unknown change")

        self.assertFalse(result.resolved)
        self.assertEqual(result.escalation_reason, EscalationReason.LOW_CONFIDENCE)

    def test_security_risk_triggers_escalation(self):
        """安全风险应触发升级"""
        shadow_agents = [
            self._create_mock_agent(MinimalVote(
                vote=VoteEnum.APPROVE,
                confidence=0.9,
                risks=[RiskCategory.SECURITY]
            )),
        ]

        facilitator = ShadowFacilitator(shadow_agents=shadow_agents)
        result = facilitator.deliberate("Auth change")

        self.assertFalse(result.resolved)
        self.assertEqual(result.escalation_reason, EscalationReason.CRITICAL_RISK)

    def test_stats_tracking(self):
        """统计跟踪应正确"""
        shadow_agents = [
            self._create_mock_agent(MinimalVote(vote=VoteEnum.APPROVE, confidence=0.9)),
        ]

        facilitator = ShadowFacilitator(shadow_agents=shadow_agents)

        # 第一次审议 - 通过
        facilitator.deliberate("Simple fix")

        stats = facilitator.get_stats()
        self.assertEqual(stats["total_deliberations"], 1)
        self.assertEqual(stats["shadow_resolved"], 1)
        self.assertEqual(stats["escalations"], 0)
        self.assertEqual(stats["resolution_rate_percent"], 100.0)


class TestShadowResult(unittest.TestCase):
    def test_result_creation(self):
        """结果创建应正常"""
        result = ShadowResult(
            resolved=True,
            decision=ConsensusDecision.AUTO_COMMIT,
            shadow_votes=[],
            cost_saved_percent=90.0,
        )
        self.assertTrue(result.resolved)
        self.assertIsNotNone(result.timestamp)


if __name__ == "__main__":
    unittest.main()
