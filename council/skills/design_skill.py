"""
DesignSkill - 架构设计技能

组合工具实现自动化架构设计:
1. 分析需求
2. 生成 Mermaid 图 (流程图、时序图、类图)
3. 生成 Markdown 设计文档
"""

from typing import Dict, Any, List, Optional, Callable
from pydantic import BaseModel, Field
import asyncio
import logging
import os
from .base_skill import BaseSkill
from council.tools.file_system import FileTools
from council.observability.tracer import AgentTracer
from council.prompts import load_prompt

logger = logging.getLogger(__name__)


class DesignInput(BaseModel):
    """设计任务输入"""

    requirement: str = Field(..., description="设计需求描述")
    output_path: str = Field(..., description="输出文档路径")
    diagram_types: List[str] = Field(
        default=["flowchart", "sequence"], description="需要的图表类型"
    )


class DesignOutput(BaseModel):
    """设计任务输出"""

    doc_path: str
    diagrams_generated: List[str]
    summary: str


class DesignSkill(BaseSkill):
    """
    架构设计技能 (DesignSkill)

    能力:
    - 分析需求并生成架构设计文档
    - 自动生成 Mermaid 图表
    - 结构化文档生成 (背景、架构、API、数据模型)

    Features:
    - 模板化文档生成
    - Mermaid 集成
    - OpenTelemetry 追踪
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
            name="DesignSkill",
            description="Automated architecture design and documentation generation",
            llm_client=llm_client,
            approval_callback=approval_callback,
            progress_callback=progress_callback,
        )
        self.working_dir = os.path.abspath(working_dir)
        self.file_tools = FileTools(root_dir=self.working_dir)
        self.tracer = tracer or AgentTracer("design-skill")

    async def execute(
        self,
        requirement: str,
        output_path: str,
        diagram_types: Optional[List[str]] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        执行设计任务

        Args:
            requirement: 需求描述
            output_path: 输出路径
            diagram_types: 图表类型
        """
        if diagram_types is None:
            diagram_types = ["flowchart", "sequence"]

        try:
            input_data = DesignInput(
                requirement=requirement,
                output_path=output_path,
                diagram_types=diagram_types,
            )
        except Exception as e:
            logger.error(f"Input validation failed: {e}")
            raise ValueError(f"Invalid input: {e}")

        with self.tracer.trace_agent_step("DesignSkill", "execute") as span:
            # 限制输入长度，防止 Token 爆炸
            truncated_requirement = input_data.requirement[:10000]
            if len(input_data.requirement) > 10000:
                logger.warning("Design requirement truncated to 10000 chars")
                truncated_requirement += "...(truncated)"

            span.set_attribute("requirement", truncated_requirement[:100])

            logger.info(f"🎨 [DesignSkill] 开始设计: {truncated_requirement[:50]}...")

            try:
                # 1. 生成文档内容
                with self.tracer.trace_llm_call(
                    "doc_generator",
                    f"Generate design doc for {input_data.requirement[:50]}",
                ):
                    content = await self._generate_doc_content(
                        input_data.requirement, input_data.diagram_types
                    )

                # 2. 写入文件
                result = self.file_tools.write_file(input_data.output_path, content)

                if "Error" in result:
                    raise RuntimeError(f"Failed to write design doc: {result}")

                logger.info(
                    f"📝 [DesignSkill] 已生成设计文档: {input_data.output_path}"
                )

                output = DesignOutput(
                    doc_path=input_data.output_path,
                    diagrams_generated=input_data.diagram_types,
                    summary=f"成功生成设计文档 {input_data.output_path}, 包含 {len(input_data.diagram_types)} 个图表",
                )

                return output.model_dump()

            except Exception as e:
                logger.error(f"Design task failed: {e}", exc_info=True)
                span.set_attribute("error", str(e))
                raise RuntimeError(f"Design task failed: {e}")

    async def _generate_doc_content(
        self, requirement: str, diagram_types: List[str]
    ) -> str:
        """生成文档内容"""
        if self.llm_client:
            # 实际 LLM 调用
            # 实际 LLM 调用
            prompt_template = load_prompt("design_skill")
            prompt = prompt_template.format(
                requirement=requirement, diagram_types=", ".join(diagram_types)
            )
            complete = getattr(self.llm_client, "complete", None)
            if not callable(complete):
                raise NotImplementedError("llm_client must provide complete()")
            result = complete(prompt)
            if asyncio.iscoroutine(result):
                result = await result
            return result

        # 模拟生成
        content = f"# 架构设计文档: {requirement[:30]}...\n\n"
        content += "## 1. 背景与目标\n\n自动生成的架构设计文档。\n\n"

        content += "## 2. 架构概览\n\n"
        if "flowchart" in diagram_types:
            content += "```mermaid\ngraph TD\n    A[User] --> B[System]\n    B --> C[Database]\n```\n\n"

        content += "## 3. 核心流程\n\n"
        if "sequence" in diagram_types:
            content += "```mermaid\nsequenceDiagram\n    User->>System: Request\n    System->>Database: Query\n    Database-->>System: Data\n    System-->>User: Response\n```\n\n"

        return content
