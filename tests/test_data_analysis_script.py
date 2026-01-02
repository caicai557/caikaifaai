import sys
from unittest.mock import MagicMock

# Mock litellm before any council imports
sys.modules["litellm"] = MagicMock()

import pytest
import os
import shutil
from council.skills.data_analysis_skill import DataAnalysisSkill


@pytest.fixture
def skill_with_mock_llm():
    """Create skill with a mock LLM that returns a valid script"""
    llm = MagicMock()
    # Mock complete() to return a script that actually runs
    llm.complete.return_value = """
import os
import sys

def main():
    print("Starting analysis...")
    output_dir = "analysis_output"
    os.makedirs(output_dir, exist_ok=True)

    # Mock Analysis
    with open(f"{output_dir}/report.md", "w") as f:
        f.write("# Analysis Report\\n\\nGoal: Test\\n\\nResult: Success")

    # Mock Chart
    with open(f"{output_dir}/chart.png", "w") as f:
        f.write("PNG_DATA")

    print("Analysis complete.")

if __name__ == "__main__":
    main()
"""
    return DataAnalysisSkill(llm_client=llm, working_dir=".")


@pytest.mark.asyncio
async def test_script_execution(skill_with_mock_llm):
    """Test that the skill generates and executes a script"""

    # Cleanup before test
    if os.path.exists("analysis_output"):
        shutil.rmtree("analysis_output")

    result = await skill_with_mock_llm.execute(
        data_file="dummy.csv", goal="Test Goal", output_dir="analysis_output"
    )

    # Verify output structure
    assert "report_path" in result
    assert "charts" in result
    assert len(result["charts"]) == 1
    assert result["charts"][0].endswith("chart.png")

    # Verify files exist
    assert os.path.exists("analysis_output/analysis_script.py")
    assert os.path.exists("analysis_output/report.md")
    assert os.path.exists("analysis_output/chart.png")

    # Verify script content
    with open("analysis_output/analysis_script.py") as f:
        content = f.read()
        assert "def main():" in content

    # Cleanup
    shutil.rmtree("analysis_output")
