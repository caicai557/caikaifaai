"""
Tests for Protocol Schema

验证 Pydantic 模型的约束和转换功能。
"""

import unittest
import sys
import os

sys.path.append(os.getcwd())

from council.protocol.schema import (
    VoteEnum,
    RiskCategory,
    MinimalVote,
    MinimalThinkResult,
    DebateMessage,
)
from pydantic import ValidationError


class TestVoteEnum(unittest.TestCase):
    def test_vote_values(self):
        self.assertEqual(VoteEnum.REJECT, 0)
        self.assertEqual(VoteEnum.APPROVE, 1)
        self.assertEqual(VoteEnum.APPROVE_WITH_CHANGES, 2)
        self.assertEqual(VoteEnum.HOLD, 3)
        
    def test_to_legacy(self):
        self.assertEqual(VoteEnum.APPROVE.to_legacy(), "approve")
        self.assertEqual(VoteEnum.REJECT.to_legacy(), "reject")


class TestMinimalVote(unittest.TestCase):
    def test_valid_vote(self):
        vote = MinimalVote(vote=1, confidence=0.9, risks=["sec"])
        self.assertEqual(vote.vote, VoteEnum.APPROVE)
        self.assertEqual(vote.confidence, 0.9)
        self.assertEqual(vote.risks, [RiskCategory.SECURITY])
        
    def test_confidence_bounds(self):
        # Valid bounds
        vote = MinimalVote(vote=0, confidence=0.0)
        self.assertEqual(vote.confidence, 0.0)
        
        vote = MinimalVote(vote=0, confidence=1.0)
        self.assertEqual(vote.confidence, 1.0)
        
        # Invalid: out of bounds
        with self.assertRaises(ValidationError):
            MinimalVote(vote=0, confidence=1.5)
            
        with self.assertRaises(ValidationError):
            MinimalVote(vote=0, confidence=-0.1)
            
    def test_blocking_reason_max_length(self):
        # Valid: under limit
        vote = MinimalVote(vote=0, confidence=0.5, blocking_reason="SQL Injection risk")
        self.assertIsNotNone(vote.blocking_reason)
        
        # Invalid: over limit (100 chars)
        with self.assertRaises(ValidationError):
            MinimalVote(vote=0, confidence=0.5, blocking_reason="x" * 101)
            
    def test_to_legacy_dict(self):
        vote = MinimalVote(vote=1, confidence=0.85, blocking_reason="Minor issue")
        legacy = vote.to_legacy_dict()
        
        self.assertEqual(legacy["decision"], "approve")
        self.assertEqual(legacy["confidence"], 0.85)
        self.assertEqual(legacy["rationale"], "Minor issue")


class TestMinimalThinkResult(unittest.TestCase):
    def test_valid_result(self):
        result = MinimalThinkResult(
            summary="Architecture looks good",
            concerns=["Scalability"],
            suggestions=["Add caching"],
            confidence=0.8
        )
        self.assertEqual(result.summary, "Architecture looks good")
        self.assertEqual(len(result.concerns), 1)
        
    def test_summary_max_length(self):
        with self.assertRaises(ValidationError):
            MinimalThinkResult(
                summary="x" * 201,  # Over 200 char limit
                confidence=0.5
            )
            
    def test_lists_truncation(self):
        # Should truncate to 5 items max
        result = MinimalThinkResult(
            summary="Test",
            concerns=["c1", "c2", "c3", "c4", "c5", "c6", "c7"],
            suggestions=[],
            confidence=0.5
        )
        self.assertEqual(len(result.concerns), 5)


class TestDebateMessage(unittest.TestCase):
    def test_valid_message(self):
        msg = DebateMessage(
            agent="Architect",
            message_type="vote",
            content="I approve this design",
        )
        self.assertEqual(msg.agent, "Architect")
        
    def test_invalid_message_type(self):
        with self.assertRaises(ValidationError):
            DebateMessage(
                agent="Architect",
                message_type="invalid_type",  # Not in allowed pattern
                content="Test"
            )


if __name__ == "__main__":
    unittest.main()
