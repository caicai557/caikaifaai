"""
Unit tests for Wald Consensus Algorithm (SPRT)

Tests cover:
- Auto-commit threshold (π ≥ 0.95)
- Reject threshold (π ≤ 0.30)
- Hold-for-human (intermediate values)
- Empty votes handling
- Semantic entropy calculation
"""

import pytest
from council.facilitator.wald_consensus import (
    WaldConsensus,
    WaldConfig,
    ConsensusResult,
    ConsensusDecision,
)


class TestWaldConsensusAutoCommit:
    """Tests for auto-commit threshold (π ≥ 0.95)"""

    def test_unanimous_high_confidence_approval(self):
        """All agents approve with high confidence → AUTO_COMMIT"""
        detector = WaldConsensus()
        votes = [
            {"agent": "Architect", "decision": "approve", "confidence": 0.95},
            {"agent": "Coder", "decision": "approve", "confidence": 0.90},
            {"agent": "SecurityAuditor", "decision": "approve", "confidence": 0.85},
        ]
        result = detector.evaluate(votes)
        assert result.decision == ConsensusDecision.AUTO_COMMIT
        assert result.pi_approve >= 0.95

    def test_approve_with_changes_counts_as_approve(self):
        """approve_with_changes should be treated as approval"""
        detector = WaldConsensus()
        votes = [
            {
                "agent": "Architect",
                "decision": "approve_with_changes",
                "confidence": 0.90,
            },
            {"agent": "Coder", "decision": "approve", "confidence": 0.95},
            {
                "agent": "SecurityAuditor",
                "decision": "approve_with_changes",
                "confidence": 0.88,
            },
        ]
        result = detector.evaluate(votes)
        assert result.decision == ConsensusDecision.AUTO_COMMIT


class TestWaldConsensusReject:
    """Tests for reject threshold (π ≤ 0.30)"""

    def test_unanimous_high_confidence_rejection(self):
        """All agents reject with high confidence → REJECT"""
        detector = WaldConsensus()
        votes = [
            {"agent": "Architect", "decision": "reject", "confidence": 0.95},
            {"agent": "Coder", "decision": "reject", "confidence": 0.90},
            {"agent": "SecurityAuditor", "decision": "reject", "confidence": 0.95},
        ]
        result = detector.evaluate(votes)
        assert result.decision == ConsensusDecision.REJECT
        assert result.pi_approve <= 0.30

    def test_majority_rejection(self):
        """Majority reject → likely REJECT"""
        detector = WaldConsensus()
        votes = [
            {"agent": "Architect", "decision": "reject", "confidence": 0.85},
            {"agent": "Coder", "decision": "reject", "confidence": 0.80},
            {"agent": "SecurityAuditor", "decision": "hold", "confidence": 0.50},
        ]
        result = detector.evaluate(votes)
        assert result.decision == ConsensusDecision.REJECT


class TestWaldConsensusHoldForHuman:
    """Tests for hold-for-human (intermediate values)"""

    def test_mixed_votes_with_uncertainty(self):
        """Mixed votes with low confidence → HOLD_FOR_HUMAN"""
        detector = WaldConsensus()
        votes = [
            {"agent": "Architect", "decision": "approve", "confidence": 0.60},
            {"agent": "Coder", "decision": "hold", "confidence": 0.50},
            {"agent": "SecurityAuditor", "decision": "reject", "confidence": 0.55},
        ]
        result = detector.evaluate(votes)
        assert result.decision == ConsensusDecision.HOLD_FOR_HUMAN
        assert 0.30 < result.pi_approve < 0.95

    def test_all_hold_votes(self):
        """All agents hold → HOLD_FOR_HUMAN"""
        detector = WaldConsensus()
        votes = [
            {"agent": "Architect", "decision": "hold", "confidence": 0.50},
            {"agent": "Coder", "decision": "hold", "confidence": 0.50},
            {"agent": "SecurityAuditor", "decision": "hold", "confidence": 0.50},
        ]
        result = detector.evaluate(votes)
        assert result.decision == ConsensusDecision.HOLD_FOR_HUMAN


class TestWaldConsensusEdgeCases:
    """Edge case tests"""

    def test_empty_votes(self):
        """Empty votes list → HOLD_FOR_HUMAN with neutral probabilities"""
        detector = WaldConsensus()
        result = detector.evaluate([])
        assert result.decision == ConsensusDecision.HOLD_FOR_HUMAN
        assert result.pi_approve == 0.5
        assert result.pi_reject == 0.5
        assert "没有收到任何投票" in result.reason

    def test_single_vote_high_confidence_approve(self):
        """Single high-confidence approve vote"""
        detector = WaldConsensus()
        votes = [{"agent": "Architect", "decision": "approve", "confidence": 0.99}]
        result = detector.evaluate(votes)
        # Single vote may not reach threshold depending on prior
        assert result.pi_approve > 0.5

    def test_custom_config_thresholds(self):
        """Custom config with different thresholds"""
        config = WaldConfig(upper_limit=0.80, lower_limit=0.20, prior_approve=0.50)
        detector = WaldConsensus(config)
        votes = [
            {"agent": "Architect", "decision": "approve", "confidence": 0.80},
            {"agent": "Coder", "decision": "approve", "confidence": 0.75},
        ]
        result = detector.evaluate(votes)
        # With lower threshold, should auto-commit easier
        assert (
            result.pi_approve >= 0.80
            or result.decision == ConsensusDecision.AUTO_COMMIT
        )


class TestWaldConsensusSemanticEntropy:
    """Tests for semantic entropy calculation"""

    def test_entropy_unanimous_decision(self):
        """All same decision → entropy = 0"""
        detector = WaldConsensus()
        votes = [
            {"agent": "A", "decision": "approve", "confidence": 0.9},
            {"agent": "B", "decision": "approve", "confidence": 0.8},
            {"agent": "C", "decision": "approve", "confidence": 0.85},
        ]
        entropy = detector.get_semantic_entropy(votes)
        assert entropy == 0.0

    def test_entropy_mixed_decisions(self):
        """Mixed decisions → entropy > 0"""
        detector = WaldConsensus()
        votes = [
            {"agent": "A", "decision": "approve", "confidence": 0.9},
            {"agent": "B", "decision": "reject", "confidence": 0.8},
            {"agent": "C", "decision": "hold", "confidence": 0.5},
        ]
        entropy = detector.get_semantic_entropy(votes)
        assert entropy > 0.0
        assert entropy <= 1.0

    def test_entropy_empty_votes(self):
        """Empty votes → maximum entropy (1.0)"""
        detector = WaldConsensus()
        entropy = detector.get_semantic_entropy([])
        assert entropy == 1.0

    def test_entropy_binary_split(self):
        """50/50 split → high entropy"""
        detector = WaldConsensus()
        votes = [
            {"agent": "A", "decision": "approve", "confidence": 0.9},
            {"agent": "B", "decision": "reject", "confidence": 0.9},
        ]
        entropy = detector.get_semantic_entropy(votes)
        # Binary split should have entropy close to 0.5 (normalized)
        assert entropy > 0.4


class TestWaldConsensusShouldContinue:
    """Tests for should_continue logic"""

    def test_should_not_continue_after_auto_commit(self):
        """After AUTO_COMMIT, should not continue"""
        detector = WaldConsensus()
        result = ConsensusResult(
            decision=ConsensusDecision.AUTO_COMMIT,
            pi_approve=0.98,
            pi_reject=0.02,
            likelihood_ratio=10.0,
            votes_summary=[],
            reason="Auto-committed",
            iteration=2,
        )
        assert detector.should_continue(result, max_iterations=5) is False

    def test_should_not_continue_after_reject(self):
        """After REJECT, should not continue"""
        detector = WaldConsensus()
        result = ConsensusResult(
            decision=ConsensusDecision.REJECT,
            pi_approve=0.15,
            pi_reject=0.85,
            likelihood_ratio=0.1,
            votes_summary=[],
            reason="Rejected",
            iteration=2,
        )
        assert detector.should_continue(result, max_iterations=5) is False

    def test_should_continue_hold_for_human(self):
        """HOLD_FOR_HUMAN and under max_iterations → should continue"""
        detector = WaldConsensus()
        result = ConsensusResult(
            decision=ConsensusDecision.HOLD_FOR_HUMAN,
            pi_approve=0.60,
            pi_reject=0.40,
            likelihood_ratio=1.5,
            votes_summary=[],
            reason="Needs human review",
            iteration=2,
        )
        assert detector.should_continue(result, max_iterations=5) is True

    def test_should_not_continue_at_max_iterations(self):
        """At max_iterations, should not continue"""
        detector = WaldConsensus()
        result = ConsensusResult(
            decision=ConsensusDecision.HOLD_FOR_HUMAN,
            pi_approve=0.60,
            pi_reject=0.40,
            likelihood_ratio=1.5,
            votes_summary=[],
            reason="Needs human review",
            iteration=5,
        )
        assert detector.should_continue(result, max_iterations=5) is False


class TestWaldConfigValidation:
    """Tests for WaldConfig validation"""

    def test_valid_config(self):
        """Valid config should not raise"""
        config = WaldConfig(upper_limit=0.95, lower_limit=0.30, prior_approve=0.70)
        assert config.upper_limit == 0.95
        assert config.lower_limit == 0.30

    def test_invalid_config_limits_order(self):
        """lower_limit >= upper_limit should raise"""
        with pytest.raises(AssertionError):
            WaldConfig(upper_limit=0.30, lower_limit=0.95, prior_approve=0.70)

    def test_invalid_config_prior_out_of_range(self):
        """prior_approve out of (0, 1) should raise"""
        with pytest.raises(AssertionError):
            WaldConfig(upper_limit=0.95, lower_limit=0.30, prior_approve=1.5)
