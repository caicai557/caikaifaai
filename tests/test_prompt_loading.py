import pytest
from unittest.mock import MagicMock, AsyncMock
from council.skills.coding_skill import CodingSkill
from council.skills.design_skill import DesignSkill
from council.skills.research_skill import ResearchSkill
from council.skills.data_analysis_skill import DataAnalysisSkill


@pytest.fixture
def mock_llm():
    llm = MagicMock()
    llm.complete = AsyncMock(return_value="Mock LLM Response")
    return llm


@pytest.mark.asyncio
async def test_coding_skill_prompt_loading(mock_llm):
    skill = CodingSkill(llm_client=mock_llm)
    # Trigger generation which uses the prompt
    await skill._generate_code("Task", {}, "target.py")

    # Verify LLM was called
    assert mock_llm.complete.called
    # Verify prompt contains template text
    call_args = mock_llm.complete.call_args[0][0]
    assert "任务:" in call_args
    assert "目标文件:" in call_args


@pytest.mark.asyncio
async def test_design_skill_prompt_loading(mock_llm):
    skill = DesignSkill(llm_client=mock_llm)
    await skill._generate_doc_content("Req", ["ClassDiagram"])

    assert mock_llm.complete.called
    call_args = mock_llm.complete.call_args[0][0]
    assert "需求:" in call_args
    assert "图表类型:" in call_args


@pytest.mark.asyncio
async def test_research_skill_prompt_loading(mock_llm):
    skill = ResearchSkill(llm_client=mock_llm)
    await skill._summarize("Topic", ["Source 1"])

    assert mock_llm.complete.called
    call_args = mock_llm.complete.call_args[0][0]
    assert "Topic:" in call_args
    assert "Sources:" in call_args


@pytest.mark.asyncio
async def test_data_analysis_skill_prompt_loading(mock_llm):
    skill = DataAnalysisSkill(llm_client=mock_llm)
    await skill._generate_analysis_code("data.csv", "Goal", "out")

    assert mock_llm.complete.called
    call_args = mock_llm.complete.call_args[0][0]
    assert "Data file:" in call_args
    assert "Goal:" in call_args
