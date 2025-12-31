import unittest
import sys
import os

# Add project root
sys.path.append(os.getcwd())

from council.mcp.ai_council_server import AICouncilServer, ModelResponse, ModelProvider
from council.facilitator.wald_consensus import ConsensusDecision


class TestServerConsensus(unittest.IsolatedAsyncioTestCase):
    def test_parse_vote_approve(self):
        """Test parsing an APPROVE vote from model response"""
        server = AICouncilServer(models=[])
        content = """I have analyzed the code.
        Vote: APPROVE
        Confidence: 0.95
        Rationale: Looks good.
        """
        vote = server._parse_vote(content, "TestAgent")

        self.assertEqual(vote.get("decision"), "approve")
        self.assertEqual(vote.get("confidence"), 0.95)
        self.assertEqual(vote.get("agent"), "TestAgent")

    def test_parse_vote_reject(self):
        """Test parsing a REJECT vote"""
        server = AICouncilServer(models=[])
        content = "VOTE: REJECT\nCONFIDENCE: 0.8"
        vote = server._parse_vote(content, "TestAgent")

        self.assertEqual(vote.get("decision"), "reject")
        self.assertEqual(vote.get("confidence"), 0.8)

    def test_evaluate_votes_autocommit(self):
        """Test evaluate_votes returns AUTO_COMMIT with strong support"""
        server = AICouncilServer(models=[])

        # Simulate high agreement responses
        responses = [
            ModelResponse(
                provider=ModelProvider.GEMINI,
                model_name="gemini",
                content="Vote: APPROVE\nConfidence: 0.99",
                latency_ms=100,
                success=True,
            ),
            ModelResponse(
                provider=ModelProvider.OPENAI,
                model_name="gpt-4",
                content="Vote: APPROVE\nConfidence: 0.98",
                latency_ms=100,
                success=True,
            ),
        ]

        # Mock WaldConsensus to return AUTO_COMMIT
        # Note: In real implementation we'll use the actual class,
        # but here we want to test the integration logic.
        # Ideally we let the real WaldConsensus run if logic is simple.

        result = server.evaluate_votes(responses)
        self.assertEqual(result.decision, ConsensusDecision.AUTO_COMMIT)
        self.assertTrue(result.pi_approve > 0.9)

    def test_evaluate_votes_no_valid_votes(self):
        """Test with responses that aren't votes"""
        server = AICouncilServer(models=[])
        responses = [
            ModelResponse(
                provider=ModelProvider.GEMINI,
                model_name="gemini",
                content="Just chatting, no vote here.",
                latency_ms=100,
                success=True,
            )
        ]

        result = server.evaluate_votes(responses)
        self.assertEqual(result.decision, ConsensusDecision.HOLD_FOR_HUMAN)


if __name__ == "__main__":
    unittest.main()
