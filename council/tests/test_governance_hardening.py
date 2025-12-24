
import unittest
import sys
import os
from unittest.mock import MagicMock

# Add project root
sys.path.append(os.getcwd())

from council.governance.gateway import GovernanceGateway, ActionType, RiskLevel, ApprovalRequest
from council.facilitator.wald_consensus import ConsensusResult, ConsensusDecision

class TestGovernanceHardening(unittest.TestCase):
    
    def test_scan_content_dangerous_rm_rf(self):
        """Test blocking of recursive deletion commands in content"""
        gateway = GovernanceGateway()
        content = "import os\nos.system('rm -rf /')"
        
        # Note: _scan_content is internal, but we test it for hardening verification
        risk = gateway._scan_content(content)
        self.assertEqual(risk, RiskLevel.CRITICAL)

    def test_scan_content_suspicious_eval(self):
        """Test detection of eval()"""
        gateway = GovernanceGateway()
        content = "eval('__import__(\"os\").system(\"ls\")')"
        
        risk = gateway._scan_content(content)
        self.assertIn(risk, [RiskLevel.HIGH, RiskLevel.MEDIUM])

    def test_requires_approval_with_content(self):
        """Test requires_approval checks content"""
        gateway = GovernanceGateway()
        content = "os.system('mkfs /dev/sda')"
        
        requires = gateway.requires_approval(
            ActionType.FILE_MODIFY, 
            affected_paths=["script.py"],
            content=content
        )
        self.assertTrue(requires)

    def test_auto_approve_with_council_consensus(self):
        """Test that high confidence council consensus can auto-approve"""
        gateway = GovernanceGateway()
        
        # Create a request
        request = gateway.create_approval_request(
            ActionType.FILE_MODIFY,
            description="Fix bug",
            affected_resources=["utils.py"],
            rationale="Approved by council"
        )
        
        # Mock a strong consensus result
        consensus = ConsensusResult(
            decision=ConsensusDecision.AUTO_COMMIT,
            pi_approve=0.98,
            pi_reject=0.02,
            likelihood_ratio=100.0,
            votes_summary=[],
            reason="High agreement"
        )
        
        # Attempt auto-approve
        approved = gateway.auto_approve_with_council(request, consensus)
        
        self.assertTrue(approved)
        self.assertTrue(request.approved)
        self.assertEqual(request.approver, "council_auto_commit")

if __name__ == "__main__":
    unittest.main()
