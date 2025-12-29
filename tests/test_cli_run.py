import unittest
from unittest.mock import patch
import os
from council.cli import run_agent


class TestCLIRun(unittest.TestCase):
    def setUp(self):
        # Create a dummy agent script
        self.script_path = "tests/dummy_agent_script.py"
        with open(self.script_path, "w") as f:
            f.write("""
from council.agents.base_agent import BaseAgent, ExecuteResult

class DummyAgent(BaseAgent):
    def __init__(self):
        super().__init__("dummy", "prompt")

    def think(self, task, context=None): pass
    def vote(self, proposal, context=None): pass
    def execute(self, task, plan=None):
        return ExecuteResult(True, "Executed: " + task)

agent = DummyAgent()
""")

    def tearDown(self):
        if os.path.exists(self.script_path):
            os.remove(self.script_path)

    def test_run_agent_success(self):
        # Run
        with patch("builtins.print"):
            # We need to mock rich console if present, or just let it print
            # Since we can't easily capture rich output in this simple test without more deps,
            # we just ensure it runs without error.
            run_agent(self.script_path, "Test Task")

        # We can't easily assert the output without capturing stdout,
        # but if it didn't raise exception, it passed the loading phase.

    def test_run_agent_file_not_found(self):
        with self.assertRaises(FileNotFoundError):
            run_agent("non_existent.py", "Task")


if __name__ == "__main__":
    unittest.main()
