"""
CodingSkill - 编码技能

组合工具实现自动化编码流程:
1. 读取现有代码
2. 分析需求并生成代码
3. 运行测试验证
4. 如失败则自动修复

基于 SelfHealingLoop 的最佳实践实现。
"""

from typing import Dict, Any, List, Optional, Callable
from pydantic import BaseModel, Field
import asyncio
import subprocess
import logging
import os
import shlex
from .base_skill import BaseSkill
from council.tools.file_system import FileTools
from council.observability.tracer import AgentTracer
from council.prompts import load_prompt

logger = logging.getLogger(__name__)


class CodingInput(BaseModel):
    """编码任务输入"""

    task: str = Field(..., description="编码任务描述")
    target_file: Optional[str] = Field(None, description="目标文件路径")
    context_files: List[str] = Field(default_factory=list, description="上下文文件列表")
    max_iterations: int = Field(3, description="最大修复迭代次数", ge=1, le=10)


class CodingOutput(BaseModel):
    """编码任务输出"""

    success: bool
    files_modified: List[str]
    test_passed: bool
    iterations: int
    summary: str
    code_diff: Optional[str] = None


class CodingSkill(BaseSkill):
    """
    编码技能 (CodingSkill)

    能力:
    - 读取现有代码结构
    - 根据需求生成/修改代码
    - 运行测试验证
    - 自动修复失败的测试 (自愈循环)

    Features:
    - FileTools 集成
    - 测试驱动验证
    - 自愈循环 (最多 N 次迭代)
    - OpenTelemetry 追踪
    """

    def __init__(
        self,
        llm_client=None,
        working_dir: str = ".",
        test_command: str = "python -m pytest",
        tracer: Optional[AgentTracer] = None,
        approval_callback: Optional[Callable] = None,
        progress_callback: Optional[Callable] = None,
    ):
        super().__init__(
            name="CodingSkill",
            description="Automated coding with test validation and self-healing",
            llm_client=llm_client,
            approval_callback=approval_callback,
            progress_callback=progress_callback,
        )
        self.working_dir = os.path.abspath(working_dir)
        self.test_command = test_command
        self.file_tools = FileTools(root_dir=self.working_dir)
        self.tracer = tracer or AgentTracer("coding-skill")

    async def execute(
        self,
        task: str,
        target_file: str = None,
        context_files: List[str] = None,
        max_iterations: int = 3,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        执行编码任务

        Args:
            task: 编码任务描述
            target_file: 目标文件路径
            context_files: 上下文文件列表
            max_iterations: 最大修复迭代次数
        """
        # 验证输入
        try:
            input_data = CodingInput(
                task=task,
                target_file=target_file,
                context_files=context_files or [],
                max_iterations=max_iterations,
            )
        except Exception as e:
            logger.error(f"Input validation failed: {e}")
            raise ValueError(f"Invalid input: {e}")

        with self.tracer.trace_agent_step("CodingSkill", "execute") as span:
            span.set_attribute("task", input_data.task[:100])

            logger.info(f"💻 [CodingSkill] 开始编码任务: {input_data.task[:50]}...")

            files_modified = []
            iterations_used = 0

            try:
                # 1. 读取上下文
                context = await self._gather_context(input_data.context_files)
                logger.info(f"📖 [CodingSkill] 已读取 {len(context)} 个上下文文件")

                # 2. 生成代码
                if input_data.target_file:
                    with self.tracer.trace_llm_call(
                        "code_generator", f"Generate code for {input_data.task[:50]}"
                    ):
                        code = await self._generate_code(
                            input_data.task, context, input_data.target_file
                        )

                    if code:
                        result = self.file_tools.write_file(
                            input_data.target_file, code
                        )
                        if "Success" in result:
                            files_modified.append(input_data.target_file)
                            logger.info(
                                f"✍️ [CodingSkill] 已写入 {input_data.target_file}"
                            )
                        else:
                            raise RuntimeError(result)

                # 3. 验证循环 (自愈)
                test_passed = False
                for i in range(input_data.max_iterations):
                    iterations_used = i + 1

                    with self.tracer.trace_tool_call(
                        "test_runner", {"command": self.test_command}
                    ):
                        test_result = await self._run_tests()

                    if test_result["passed"]:
                        test_passed = True
                        logger.info(
                            f"✅ [CodingSkill] 测试通过 (迭代 {iterations_used})"
                        )
                        break

                    logger.warning(
                        f"⚠️ [CodingSkill] 测试失败 (迭代 {iterations_used}), 尝试修复..."
                    )

                    if not input_data.target_file:
                        logger.warning(
                            "No target file specified for fixing. Aborting self-healing loop."
                        )
                        break

                    # 尝试修复
                    if input_data.target_file and i < input_data.max_iterations - 1:
                        with self.tracer.trace_llm_call(
                            "code_fixer", "Fixing test failure"
                        ):
                            fixed = await self._fix_code(
                                input_data.target_file,
                                test_result["error_output"],
                                input_data.task,
                            )
                        if fixed:
                            result = self.file_tools.write_file(
                                input_data.target_file, fixed
                            )
                            if "Success" not in result:
                                raise RuntimeError(result)

                # 4. 构造输出
                output = CodingOutput(
                    success=test_passed,
                    files_modified=files_modified,
                    test_passed=test_passed,
                    iterations=iterations_used,
                    summary=f"{'✅ 测试通过' if test_passed else '⚠️ 测试未通过'}, 修改了 {len(files_modified)} 个文件, 使用了 {iterations_used} 次迭代",
                )

                return output.model_dump()

            except Exception as e:
                logger.error(f"Coding task failed: {e}", exc_info=True)
                span.set_attribute("error", str(e))
                return CodingOutput(
                    success=False,
                    files_modified=files_modified,
                    test_passed=False,
                    iterations=iterations_used,
                    summary=f"编码任务失败: {e}",
                ).model_dump()

    async def _gather_context(self, files: List[str]) -> Dict[str, str]:
        """收集上下文文件内容"""
        context = {}
        for file_path in files:
            content = self.file_tools.read_file(file_path)
            if not content.startswith("Error"):
                context[file_path] = content
        return context

    async def _generate_code(
        self, task: str, context: Dict[str, str], target_file: str
    ) -> Optional[str]:
        """生成代码 (模拟或 LLM)"""
        if self.llm_client:
            # 实际 LLM 调用
            prompt_template = load_prompt("coding_skill_gen")
            context_str = chr(10).join(
                f"--- {f} ---{chr(10)}{c[:4000]}" for f, c in context.items()
            )
            prompt = prompt_template.format(
                task=task, target_file=target_file, context_str=context_str
            )

            complete = getattr(self.llm_client, "complete", None)
            if not callable(complete):
                raise NotImplementedError("llm_client must provide complete()")
            result = complete(prompt)
            if asyncio.iscoroutine(result):
                result = await result
            return result

        # 模拟生成
        return f'''"""
自动生成的代码
任务: {task}
"""

def main():
    print("Hello from generated code")
    return True

if __name__ == "__main__":
    main()
'''

    async def _run_tests(self) -> Dict[str, Any]:
        """运行测试"""
        if not self.test_command:
            return {
                "passed": False,
                "error_output": "Test command not configured",
                "return_code": -1,
            }
        try:
            cmd = (
                shlex.split(self.test_command)
                if isinstance(self.test_command, str)
                else list(self.test_command)
            )
            result = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: subprocess.run(
                    cmd,
                    cwd=self.working_dir,
                    capture_output=True,
                    text=True,
                    timeout=120,
                ),
            )

            return {
                "passed": result.returncode == 0,
                "output": result.stdout,
                "error_output": result.stderr,
                "return_code": result.returncode,
            }
        except subprocess.TimeoutExpired:
            return {"passed": False, "error_output": "Test timeout", "return_code": -1}
        except Exception as e:
            return {"passed": False, "error_output": str(e), "return_code": -1}

    async def _fix_code(
        self, file_path: str, error: str, original_task: str
    ) -> Optional[str]:
        """尝试修复代码"""
        current_code = self.file_tools.read_file(file_path)
        if current_code.startswith("Error"):
            return None

        if self.llm_client:
            # 实际 LLM 修复
            prompt_template = load_prompt("coding_skill_fix")
            prompt = prompt_template.format(
                original_task=original_task,
                current_code=current_code[:4000],
                error=error[:4000],
            )
            complete = getattr(self.llm_client, "complete", None)
            if not callable(complete):
                raise NotImplementedError("llm_client must provide complete()")
            result = complete(prompt)
            if asyncio.iscoroutine(result):
                result = await result
            return result

        # 模拟修复
        return current_code  # 实际场景会返回修复后的代码
