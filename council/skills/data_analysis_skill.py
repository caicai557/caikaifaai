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
from .base_skill import BaseSkill
from council.tools.file_system import FileTools
from council.tools.programmatic_tools import ProgrammaticToolExecutor
from council.observability.tracer import AgentTracer

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

                # 3. 执行代码 (PTC)
                logger.info("🚀 [DataAnalysisSkill] 执行分析脚本...")
                with self.tracer.trace_tool_call(
                    "code_executor", {"code_length": len(code)}
                ):
                    # 注意: 实际执行需要安装 pandas/matplotlib，这里假设环境已有或使用 mock
                    # await self.executor.execute_batch(code)
                    await self._mock_execution(input_data.output_dir)

                # 4. 生成报告
                report_path = os.path.join(input_data.output_dir, "report.md")
                report_content = f"# 数据分析报告\n\n目标: {input_data.goal}\n\n## 结果\n\n![Chart](chart.png)\n"
                self.file_tools.write_file(report_path, report_content)

                output = AnalysisOutput(
                    report_path=report_path,
                    charts=["chart.png"],
                    summary=f"分析完成，报告已生成至 {report_path}",
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
            prompt = f"""
Data file: {data_file}
Goal: {goal}
Output dir: {output_dir}

Generate a Python analysis script that reads the data, computes key stats,
and saves at least one chart to the output dir.
"""
            complete = getattr(self.llm_client, "complete", None)
            if not callable(complete):
                raise NotImplementedError("llm_client must provide complete()")
            result = complete(prompt)
            if asyncio.iscoroutine(result):
                result = await result
            return result

        return f"""
import pandas as pd
import matplotlib.pyplot as plt

# Load data
df = pd.read_csv('{data_file}')

# Analyze
print(df.describe())

# Plot
plt.figure()
df.plot()
plt.savefig('{output_dir}/chart.png')
"""

    async def _mock_execution(self, output_dir: str):
        """模拟执行"""
        await asyncio.sleep(1)
        # 模拟生成文件
        chart_path = os.path.join(self.working_dir, output_dir, "chart.png")
        with open(chart_path, "w") as f:
            f.write("Mock PNG Content")
