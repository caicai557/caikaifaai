import unittest
from unittest.mock import patch
import sys
import os

sys.path.append(os.getcwd())

from council.agents.architect import Architect
from council.agents.coder import Coder
from council.agents.security_auditor import SecurityAuditor
from council.agents.base_agent import VoteDecision


class TestRealAgents(unittest.TestCase):
<<<<<<< HEAD

=======
>>>>>>> e2df45bcf4fae044c2ec81c7ea50a183bdc8bd86
    @patch("council.agents.base_agent.BaseAgent._call_llm")
    def test_architect_think(self, mock_llm):
        # Mock LLM response
        mock_llm.return_value = """
[Analysis]
Architecture is sound but needs caching.

[Concerns]
- Scalability
- Latency

[Suggestions]
- Add Redis
- Use CDN

[Confidence]
0.85
"""
        agent = Architect()
        result = agent.think("Design a web app")

        self.assertIn("Architecture is sound", result.analysis)
        self.assertIn("Scalability", result.concerns)
        self.assertEqual(result.confidence, 0.85)

    @patch("council.agents.base_agent.BaseAgent._call_llm")
    def test_coder_vote(self, mock_llm):
        mock_llm.return_value = """
Vote: APPROVE_WITH_CHANGES
Confidence: 0.9
Rationale: Good code but missing docs.
"""
        agent = Coder()
        vote = agent.vote("PR #123")

        self.assertEqual(vote.decision, VoteDecision.APPROVE_WITH_CHANGES)
        self.assertEqual(vote.confidence, 0.9)
        self.assertIn("missing docs", vote.rationale)

    @patch("council.agents.base_agent.BaseAgent._call_llm")
    def test_security_auditor_scan_behavior(self, mock_llm):
        # Test that security auditor maintains its specific parsing
        mock_llm.return_value = """
[Analysis]
Attack surface is large.

[Concerns]
- SQL Injection
- XSS

[Suggestions]
- Use prepared statements

[Confidence]
0.7
"""
        agent = SecurityAuditor()
        result = agent.think("Review SQL query")

        self.assertEqual(result.context.get("perspective"), "security")
        self.assertTrue(result.context.get("forced_debate"))
        self.assertIn("SQL Injection", result.concerns)


if __name__ == "__main__":
    unittest.main()
