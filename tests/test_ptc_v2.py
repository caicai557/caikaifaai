#!/usr/bin/env python3
"""
Unit tests for PTC V2 Self-Refining Execution Loop.
"""

import sys
import os

# Add scripts to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))


class TestPtcSdk:
    """Tests for ptc_sdk module."""

    def test_fetch_market_data_btc(self):
        """Test fetching BTC market data."""
        from ptc_sdk import fetch_market_data

        data = fetch_market_data("BTC")

        assert isinstance(data, list)
        assert len(data) > 0
        assert "price" in data[0]
        assert "symbol" in data[0]
        assert data[0]["symbol"] == "BTC"

    def test_fetch_market_data_unknown_symbol(self):
        """Test fetching data for unknown symbol returns default."""
        from ptc_sdk import fetch_market_data

        data = fetch_market_data("UNKNOWN")

        assert isinstance(data, list)
        assert len(data) > 0
        assert data[0]["symbol"] == "UNKNOWN"

    def test_virtual_sdk_docs_exists(self):
        """Test that SDK documentation is available."""
        from ptc_sdk import VIRTUAL_SDK_DOCS

        assert isinstance(VIRTUAL_SDK_DOCS, str)
        assert "fetch_market_data" in VIRTUAL_SDK_DOCS
        assert "save_result" in VIRTUAL_SDK_DOCS


import pytest  # noqa: E402
import importlib.util  # noqa: E402

# Check if typer is available
HAS_TYPER = importlib.util.find_spec("typer") is not None


@pytest.mark.skipif(not HAS_TYPER, reason="typer not installed")
class TestPtcV2Autofix:
    """Tests for ptc_v2_autofix module."""

    def test_extract_code_python_block(self):
        """Test extracting code from Python markdown block."""
        from ptc_v2_autofix import extract_code

        text = """
Here is the code:
```python
print("Hello")
```
"""
        code = extract_code(text)
        assert code == 'print("Hello")'

    def test_extract_code_no_block(self):
        """Test extracting code when no block exists."""
        from ptc_v2_autofix import extract_code

        text = "No code here"
        code = extract_code(text)
        assert code == ""

    def test_extract_code_generic_block(self):
        """Test extracting code from generic markdown block."""
        from ptc_v2_autofix import extract_code

        text = """
```
x = 1
```
"""
        code = extract_code(text)
        assert "x = 1" in code

    def test_call_llm_mock_first_attempt_has_bug(self):
        """Test that mock LLM produces buggy code on first attempt."""
        from ptc_v2_autofix import call_llm

        history = "SYSTEM: test\nUSER: Calculate average"
        response = call_llm(history, use_real_llm=False)

        # First attempt should have the intentional bug
        assert "price for d" in response or "BUG" in response

    def test_call_llm_mock_second_attempt_fixes_bug(self):
        """Test that mock LLM fixes code after seeing error."""
        from ptc_v2_autofix import call_llm

        history = """SYSTEM: test
USER: Calculate average
[RUNTIME ERROR]:
NameError: name 'price' is not defined"""

        response = call_llm(history, use_real_llm=False)

        # Second attempt should have the fix
        assert 'd["price"]' in response or "FIXED" in response


@pytest.mark.skipif(not HAS_TYPER, reason="typer not installed")
class TestIntegration:
    """Integration tests for the full loop."""

    def test_run_in_sandbox_simple_script(self):
        """Test running a simple script in sandbox."""
        from ptc_v2_autofix import run_in_sandbox

        stdout, stderr = run_in_sandbox('print("Hello World")')

        assert "Hello World" in stdout
        assert stderr == "" or stderr is None or len(stderr.strip()) == 0

    def test_run_in_sandbox_with_error(self):
        """Test sandbox captures errors."""
        from ptc_v2_autofix import run_in_sandbox

        stdout, stderr = run_in_sandbox('raise ValueError("Test error")')

        assert "ValueError" in stderr or "Test error" in stderr

    def test_run_in_sandbox_with_ptc_sdk(self):
        """Test sandbox can import ptc_sdk."""
        from ptc_v2_autofix import run_in_sandbox

        code = """
import ptc_sdk
data = ptc_sdk.fetch_market_data("BTC")
print(f"Got {len(data)} records")
"""
        stdout, stderr = run_in_sandbox(code)

        # Should succeed without import errors
        assert "Got" in stdout or stderr == ""
