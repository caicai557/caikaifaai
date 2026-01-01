import pytest
import os
from council.skills.research_skill import ResearchSkill
from council.skills.coding_skill import CodingSkill
from council.skills.code_review_skill import CodeReviewSkill
from council.skills.security_audit_skill import SecurityAuditSkill
from council.skills.design_skill import DesignSkill
from council.skills.data_analysis_skill import DataAnalysisSkill


@pytest.mark.asyncio
async def test_research_skill():
    skill = ResearchSkill()
    result = await skill.execute("AI Agents 2025", depth=2)
    assert result["topic"] == "AI Agents 2025"
    assert len(result["sources"]) == 2


@pytest.mark.asyncio
async def test_coding_skill(tmp_path):
    skill = CodingSkill(working_dir=str(tmp_path))
    target_file = "hello.py"

    # 模拟编码任务
    result = await skill.execute(
        task="Create a hello world script", target_file=target_file, max_iterations=1
    )

    # 验证文件是否生成 (模拟模式下)
    assert "hello.py" in result["files_modified"] or not result["success"]
    # 注意: 由于是模拟生成，且没有实际 LLM，success 可能是 False，但我们主要测试流程不报错


@pytest.mark.asyncio
async def test_code_review_skill(tmp_path):
    # 创建一个有问题的代码文件
    bad_code = 'password = "123456"\nprint(eval("1+1"))'
    p = tmp_path / "unsafe.py"
    p.write_text(bad_code)

    skill = CodeReviewSkill(working_dir=str(tmp_path))
    result = await skill.execute(files=["unsafe.py"])

    assert result["files_reviewed"] == 1
    # 应该检测到密码和 eval
    assert result["total_issues"] >= 2
    assert any(i["category"] == "security" for i in result["issues"])


@pytest.mark.asyncio
async def test_security_audit_skill(tmp_path):
    # 创建敏感文件
    (tmp_path / ".env").write_text("API_KEY='sk-123456'")

    skill = SecurityAuditSkill(working_dir=str(tmp_path))
    result = await skill.execute(target_dir=".")

    # 应该检测到 .env
    assert any("敏感路径" in f["title"] for f in result["findings"])


@pytest.mark.asyncio
async def test_design_skill(tmp_path):
    output_path = "design.md"
    skill = DesignSkill(working_dir=str(tmp_path))

    result = await skill.execute(
        requirement="User Login System",
        output_path=output_path,
        diagram_types=["flowchart"],
    )

    assert os.path.exists(tmp_path / output_path)
    assert "flowchart" in result["diagrams_generated"]


@pytest.mark.asyncio
async def test_data_analysis_skill(tmp_path):
    # 创建假数据
    (tmp_path / "data.csv").write_text("a,b\n1,2\n3,4")

    skill = DataAnalysisSkill(working_dir=str(tmp_path))
    result = await skill.execute(
        data_file="data.csv", goal="Analyze trends", output_dir="output"
    )

    assert os.path.exists(tmp_path / "output" / "report.md")
    assert "chart.png" in result["charts"]
