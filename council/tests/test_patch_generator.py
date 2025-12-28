import unittest
import sys
import os
from unittest.mock import MagicMock, patch

# Add project root
sys.path.append(os.getcwd())

from council.self_healing.patch_generator import PatchGenerator
from council.self_healing.loop import Diagnosis
<<<<<<< HEAD
=======

>>>>>>> e2df45bcf4fae044c2ec81c7ea50a183bdc8bd86

class TestPatchGenerator(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.diagnosis = Diagnosis(
            failed_test="test_example",
            error_type="AssertionError",
            error_message="Expected 1 but got 2",
            suspected_file="/tmp/example.py",
            suspected_line=10,
            root_cause="Logic error",
            suggested_fix="Change + to -",
        )
        self.file_content = "def add(a, b):\n    return a + b"

    @patch("builtins.open")
    @patch("os.path.exists")
    @patch("council.self_healing.patch_generator.PatchGenerator._call_llm")
    async def test_generate_patch_with_llm_success(
        self, mock_call_llm, mock_exists, mock_open
    ):
        # Setup mocks
        mock_exists.return_value = True
        mock_file = MagicMock()
        mock_file.__enter__.return_value.read.return_value = self.file_content
        mock_open.return_value = mock_file

        # Mock LLM response with markdown code block
<<<<<<< HEAD
        mock_call_llm.return_value = "Here is the fix:\n```python\ndef add(a, b):\n    return a - b\n```"
=======
        mock_call_llm.return_value = (
            "Here is the fix:\n```python\ndef add(a, b):\n    return a - b\n```"
        )
>>>>>>> e2df45bcf4fae044c2ec81c7ea50a183bdc8bd86

        generator = PatchGenerator()
        patch_result = await generator.generate_patch_with_llm(self.diagnosis)

        self.assertIn("return a - b", patch_result.patched_content)
        self.assertTrue(patch_result.confidence > 0.5)

    def test_extract_code_block(self):
        generator = PatchGenerator()
        text = "```python\ncode\n```"
        self.assertEqual(generator._extract_code_block(text), "code")

    def test_construct_prompt(self):
        generator = PatchGenerator()
        prompt = generator._construct_prompt(self.diagnosis, self.file_content)
        self.assertIn("AssertionError", prompt)
