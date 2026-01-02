import sys
from unittest.mock import MagicMock

# Mock litellm before any council imports
sys.modules["litellm"] = MagicMock()

import pytest
from council.skills.data_analysis_skill import DataAnalysisSkill


@pytest.fixture
def skill_with_mock_llm(tmp_path):
    """Create skill with a mock LLM that returns a valid script"""
    llm = MagicMock()
    llm.structured_completion = None  # Force fallback to complete()
    # Mock complete() to return a script that actually runs
    llm.complete = MagicMock(
        return_value=f'''
import os

def main():
    print("Starting analysis...")
    output_dir = "{tmp_path}/analysis_output"
    os.makedirs(output_dir, exist_ok=True)

    # Mock Analysis
    with open(f"{{output_dir}}/report.md", "w") as f:
        f.write("# Analysis Report\\n\\nGoal: Test\\n\\nResult: Success")

    # Mock Chart
    with open(f"{{output_dir}}/chart.png", "w") as f:
        f.write("PNG_DATA")

    print("Analysis complete.")

if __name__ == "__main__":
    main()
'''
    )
    return DataAnalysisSkill(llm_client=llm, working_dir=str(tmp_path)), tmp_path


@pytest.mark.asyncio
async def test_script_execution(skill_with_mock_llm):
    """Test that the skill generates and executes a script"""
    skill, tmp_path = skill_with_mock_llm

    result = await skill.execute(
        data_file="dummy.csv", goal="Test Goal", output_dir="analysis_output"
    )

    # Verify output structure
    assert "report_path" in result
    assert "charts" in result

    # Verify script was generated
    script_path = tmp_path / "analysis_output" / "analysis_script.py"
    assert script_path.exists()

    # Script content verification
    content = script_path.read_text()
    assert "def main():" in content
