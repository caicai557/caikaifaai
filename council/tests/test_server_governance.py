
import unittest
from unittest.mock import MagicMock, patch
import sys
import os

sys.path.append(os.getcwd())

from council.mcp.ai_council_server import AICouncilServer

# Use IsolatedAsyncioTestCase for async tests
class TestServerGovernance(unittest.IsolatedAsyncioTestCase):

    @patch("council.mcp.ai_council_server.AICouncilServer.query_parallel")
    @patch("council.mcp.ai_council_server.AICouncilServer._synthesize_responses")
    async def test_governance_blocking(self, mock_synthesize, mock_query_parallel):
        # Mock responses
        mock_query_parallel.return_value = []

        # Mock synthesis returning dangerous content
        mock_synthesize.return_value = "Run os.system('rm -rf /') to clean up."

        server = AICouncilServer()

        # Override gateway scanning just to be sure we hit the blocking path
        # (Though real gateway would also catch it due to our regex)
        from council.governance.gateway import RiskLevel
        server.gateway = MagicMock()
        server.gateway._scan_content.return_value = RiskLevel.CRITICAL

        response = await server.query("How to delete everything?")

        # Expect blockage
        self.assertIn("[GOVERNANCE BLOCKED]", response.synthesis)
        self.assertNotIn("rm -rf", response.synthesis)

if __name__ == "__main__":
    unittest.main()
