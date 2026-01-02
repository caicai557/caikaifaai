"""Test structured output schemas validation"""

import sys
from unittest.mock import MagicMock
import os

# Mock litellm before imports
sys.modules["litellm"] = MagicMock()
os.environ["OPENAI_API_KEY"] = "dummy"

import pytest
from council.skills.schemas import (
    GeneratedCodeOutput,
    AnalysisCodeOutput,
    SummaryOutput,
    CodeFixOutput,
)


def test_generated_code_output():
    """Test GeneratedCodeOutput schema validation"""
    output = GeneratedCodeOutput(
        code="def hello(): pass", language="python", explanation="A simple function"
    )
    assert output.code == "def hello(): pass"
    assert output.language == "python"


def test_analysis_code_output():
    """Test AnalysisCodeOutput schema validation"""
    output = AnalysisCodeOutput(
        code="import pandas as pd\ndf = pd.read_csv('data.csv')",
        imports=["pandas"],
        explanation="Load CSV data",
    )
    assert "pandas" in output.code
    assert "pandas" in output.imports


def test_summary_output():
    """Test SummaryOutput schema validation"""
    output = SummaryOutput(
        summary="This is a summary", key_points=["Point 1", "Point 2"], confidence=0.9
    )
    assert output.summary == "This is a summary"
    assert len(output.key_points) == 2
    assert output.confidence == 0.9


def test_code_fix_output():
    """Test CodeFixOutput schema validation"""
    output = CodeFixOutput(
        fixed_code="def fixed(): return True",
        changes_made=["Fixed syntax error"],
        root_cause="Missing return statement",
    )
    assert "fixed" in output.fixed_code
    assert len(output.changes_made) == 1


def test_summary_output_confidence_bounds():
    """Test confidence is bounded 0-1"""
    with pytest.raises(ValueError):
        SummaryOutput(summary="test", confidence=1.5)

    with pytest.raises(ValueError):
        SummaryOutput(summary="test", confidence=-0.1)
