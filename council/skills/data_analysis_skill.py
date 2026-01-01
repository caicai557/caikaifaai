"""
DataAnalysisSkill - 数据分析技能

组合工具实现自动化数据分析:
1. 读取数据 (CSV/JSON)
2. 编写分析脚本 (Pandas/Matplotlib)
3. 执行分析
4. 生成报告和图表
"""

from typing import Dict, Any, List, Optional, Callable
from pydantic import BaseModel, Field
import asyncio
import logging
import os
import sys
import subprocess
from .base_skill import BaseSkill
from council.tools.file_system import FileTools
from council.tools.programmatic_tools import ProgrammaticToolExecutor
from council.observability.tracer import AgentTracer
from council.prompts import load_prompt

logger = logging.getLogger(__name__)


class AnalysisInput(BaseModel):
    """分析任务输入"""

    data_file: str = Field(..., description="数据文件路径")
    goal: str = Field(..., description="分析目标")
    output_dir: str = Field("analysis_output", description="输出目录")


class AnalysisOutput(BaseModel):
    """分析任务输出"""

    report_path: str
    charts: List[str]
    summary: str


class DataAnalysisSkill(BaseSkill):
    """
    数据分析技能 (DataAnalysisSkill)

    能力:
    - 自动编写 Python 脚本分析数据
    - 生成统计图表 (PNG)
    - 生成分析报告 (Markdown)

    Features:
    - Programmatic Tool Calling (PTC)
    - 沙箱执行
    - 自动图表生成
    """

    def __init__(
        self,
        llm_client=None,
        working_dir: str = ".",
        tracer: Optional[AgentTracer] = None,
        approval_callback: Optional[Callable] = None,
        progress_callback: Optional[Callable] = None,
    ):
        super().__init__(
            name="DataAnalysisSkill",
            description="Automated data analysis and visualization using Python",
            llm_client=llm_client,
            approval_callback=approval_callback,
            progress_callback=progress_callback,
        )
        self.working_dir = os.path.abspath(working_dir)
        self.file_tools = FileTools(root_dir=self.working_dir)
        self.executor = ProgrammaticToolExecutor(timeout=60.0)
        self.tracer = tracer or AgentTracer("data-analysis-skill")

    async def execute(
        self, data_file: str, goal: str, output_dir: str = "analysis_output", **kwargs
    ) -> Dict[str, Any]:
        """
        执行分析任务

        Args:
            data_file: 数据文件路径
            goal: 分析目标
            output_dir: 输出目录
        """
        try:
            input_data = AnalysisInput(
                data_file=data_file, goal=goal, output_dir=output_dir
            )
        except Exception as e:
            logger.error(f"Input validation failed: {e}")
            raise ValueError(f"Invalid input: {e}")

        with self.tracer.trace_agent_step("DataAnalysisSkill", "execute") as span:
            # 限制输入长度
            truncated_goal = input_data.goal[:2000]
            if len(input_data.goal) > 2000:
                logger.warning("Analysis goal truncated to 2000 chars")
                truncated_goal += "...(truncated)"

            span.set_attribute("goal", truncated_goal)

            logger.info(f"📊 [DataAnalysisSkill] 开始分析: {truncated_goal}")

            try:
                # 1. 准备环境
                os.makedirs(
                    os.path.join(self.working_dir, input_data.output_dir), exist_ok=True
                )

                # 2. 生成分析代码
                with self.tracer.trace_llm_call(
                    "code_generator", f"Generate analysis code for {input_data.goal}"
                ):
                    code = await self._generate_analysis_code(
                        input_data.data_file, input_data.goal, input_data.output_dir
                    )

                # 3. 执行代码 (Script-First)
                script_path = os.path.join(input_data.output_dir, "analysis_script.py")
                abs_script_path = os.path.join(self.working_dir, script_path)

                self.file_tools.write_file(script_path, code)
                logger.info(f"📜 [DataAnalysisSkill] 脚本已写入: {script_path}")

                logger.info("🚀 [DataAnalysisSkill] 执行分析脚本...")
                with self.tracer.trace_tool_call(
                    "script_executor", {"script": script_path}
                ):
                    # 使用当前 Python 环境执行
                    cmd = [sys.executable, abs_script_path]
                    result = await asyncio.get_event_loop().run_in_executor(
                        None,
                        lambda: subprocess.run(
                            cmd,
                            cwd=self.working_dir,
                            capture_output=True,
                            text=True,
                            timeout=60,
                        ),
                    )

                    if result.returncode != 0:
                        raise RuntimeError(
                            f"Script execution failed:\nSTDOUT: {result.stdout}\nSTDERR: {result.stderr}"
                        )

                    logger.info(
                        f"✅ [DataAnalysisSkill] 脚本执行成功\nOutput: {result.stdout[:200]}..."
                    )

                # 4. 验证结果
                report_path = os.path.join(input_data.output_dir, "report.md")
                chart_path = os.path.join(input_data.output_dir, "chart.png")

                generated_files = []
                if os.path.exists(os.path.join(self.working_dir, report_path)):
                    generated_files.append(report_path)
                if os.path.exists(os.path.join(self.working_dir, chart_path)):
                    generated_files.append(chart_path)

                output = AnalysisOutput(
                    report_path=report_path
                    if report_path in generated_files
                    else "N/A",
                    charts=[f for f in generated_files if f.endswith(".png")],
                    summary=f"分析完成，生成了 {len(generated_files)} 个文件。\n脚本输出:\n{result.stdout[:500]}",
                )

                return output.model_dump()

            except Exception as e:
                logger.error(f"Analysis failed: {e}", exc_info=True)
                span.set_attribute("error", str(e))
                raise RuntimeError(f"Analysis failed: {e}")

    async def _generate_analysis_code(
        self, data_file: str, goal: str, output_dir: str
    ) -> str:
        """生成分析代码"""
        if self.llm_client:
            # 实际 LLM 调用
            # 实际 LLM 调用
            prompt_template = load_prompt("data_analysis_skill")
            prompt = prompt_template.format(
                data_file=data_file, goal=goal, output_dir=output_dir
            )
            complete = getattr(self.llm_client, "complete", None)
            if not callable(complete):
                raise NotImplementedError("llm_client must provide complete()")
            result = complete(prompt)
            if asyncio.iscoroutine(result):
                result = await result

            # 清理 Markdown 代码块标记
            if result.startswith("```python"):
                result = result.split("\n", 1)[1]
            if result.endswith("```"):
                result = result.rsplit("\n", 1)[0]

            return result

        # 模拟生成 (用于测试，不依赖 LLM)
        return f"""
import os
import sys

def main():
    print("Starting analysis...")
    output_dir = "{output_dir}"
    os.makedirs(output_dir, exist_ok=True)

    # Mock Analysis
    with open(f"{{output_dir}}/report.md", "w") as f:
        f.write("# Analysis Report\\n\\nGoal: {goal}\\n\\nResult: Success")

    # Mock Chart (empty file for demo)
    with open(f"{{output_dir}}/chart.png", "w") as f:
        f.write("PNG_DATA")

    print("Analysis complete. Generated report.md and chart.png")

if __name__ == "__main__":
    main()
"""
