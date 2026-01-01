"""
PostToolUse Hook - 工具执行后自动化钩子

在工具执行完成后触发，实现代码质量门禁和自愈循环。
"""

import asyncio
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List

from council.hooks.base import (
    BaseHook,
    HookType,
    HookAction,
    HookResult,
    HookContext,
)

logger = logging.getLogger(__name__)


@dataclass
class QualityGateResult:
    """质量门禁结果"""

    passed: bool
    gate_name: str
    message: str
    output: str = ""
    error: str = ""


class PostToolUseHook(BaseHook):
    """
    执行后置自动化钩子

    功能：
    1. 代码格式化 (ruff format)
    2. 静态检查 (ruff check)
    3. 单元测试 (pytest)
    4. 失败时触发自愈循环

    Usage:
        hook = PostToolUseHook(working_dir="/path/to/project")
        result = await hook.execute(context)
        if result.action == HookAction.RETRY:
            # 触发自愈循环
            pass
    """

    def __init__(
        self,
        working_dir: str = ".",
        enable_format: bool = True,
        enable_lint: bool = True,
        enable_test: bool = False,  # 默认关闭，避免每次修改都运行测试
        test_command: str = "python -m pytest tests/ -v --tb=short",
        lint_command: str = "ruff check",
        format_command: str = "ruff format",
        max_retries: int = 3,
        priority: int = 100,
    ):
        """
        初始化后置自动化钩子

        Args:
            working_dir: 工作目录
            enable_format: 是否启用自动格式化
            enable_lint: 是否启用静态检查
            enable_test: 是否启用测试执行
            test_command: 测试命令
            lint_command: Lint 命令
            format_command: 格式化命令
            max_retries: 最大重试次数
            priority: 优先级
        """
        super().__init__(name="post_tool_use", priority=priority)
        self.working_dir = Path(working_dir).resolve()
        self.enable_format = enable_format
        self.enable_lint = enable_lint
        self.enable_test = enable_test
        self.test_command = test_command
        self.lint_command = lint_command
        self.format_command = format_command
        self.max_retries = max_retries
        self._retry_count = 0

    @property
    def hook_type(self) -> HookType:
        return HookType.POST_TOOL_USE

    async def execute(self, context: HookContext) -> HookResult:
        """
        执行后置自动化处理

        Args:
            context: 钩子上下文

        Returns:
            HookResult: 处理结果
        """
        tool_name = context.tool_name or ""

        metadata: Dict[str, Any] = {
            "tool_name": tool_name,
            "gates_run": [],
            "gates_passed": [],
            "gates_failed": [],
        }

        # 只对文件修改类工具执行质量门禁
        file_tools = {
            "write_file",
            "edit_file",
            "replace_file",
            "create_file",
            "modify_file",
        }
        if tool_name not in file_tools:
            return HookResult(
                action=HookAction.ALLOW,
                message="No quality gates needed for this tool",
                metadata={"skipped": True, "reason": "not_file_tool"},
            )

        # 提取修改的文件路径
        modified_files = self._extract_modified_files(context.tool_args or {})
        if not modified_files:
            return HookResult(
                action=HookAction.ALLOW,
                message="No files to check",
                metadata={"skipped": True, "reason": "no_files"},
            )

        metadata["modified_files"] = modified_files
        gate_results: List[QualityGateResult] = []

        # Gate 1: 代码格式化
        if self.enable_format:
            format_result = await self._run_format(modified_files)
            gate_results.append(format_result)
            metadata["gates_run"].append("format")
            if format_result.passed:
                metadata["gates_passed"].append("format")
            else:
                metadata["gates_failed"].append("format")

        # Gate 2: 静态检查
        if self.enable_lint:
            lint_result = await self._run_lint(modified_files)
            gate_results.append(lint_result)
            metadata["gates_run"].append("lint")
            if lint_result.passed:
                metadata["gates_passed"].append("lint")
            else:
                metadata["gates_failed"].append("lint")

        # Gate 3: 单元测试
        if self.enable_test:
            test_result = await self._run_tests()
            gate_results.append(test_result)
            metadata["gates_run"].append("test")
            if test_result.passed:
                metadata["gates_passed"].append("test")
            else:
                metadata["gates_failed"].append("test")

        # 检查是否有失败的门禁
        failed_gates = [g for g in gate_results if not g.passed]
        if failed_gates:
            self._retry_count += 1
            metadata["retry_count"] = self._retry_count

            if self._retry_count >= self.max_retries:
                self._retry_count = 0
                return HookResult(
                    action=HookAction.BLOCK,
                    message=f"Quality gates failed after {self.max_retries} retries",
                    error="\n".join(
                        [f"{g.gate_name}: {g.error}" for g in failed_gates]
                    ),
                    metadata=metadata,
                )

            # 触发自愈循环
            return HookResult(
                action=HookAction.RETRY,
                message=f"Quality gates failed, triggering self-healing (attempt {self._retry_count}/{self.max_retries})",
                metadata={
                    **metadata,
                    "self_healing": True,
                    "errors": [
                        {"gate": g.gate_name, "error": g.error, "output": g.output}
                        for g in failed_gates
                    ],
                },
            )

        # 所有门禁通过
        self._retry_count = 0
        return HookResult(
            action=HookAction.ALLOW,
            message="All quality gates passed",
            metadata=metadata,
        )

    def _extract_modified_files(self, args: Dict[str, Any]) -> List[str]:
        """提取修改的文件列表"""
        files = []
        path_keys = ["path", "file", "filepath", "filename", "target_file"]
        for key in path_keys:
            if key in args:
                value = args[key]
                if isinstance(value, str) and value.endswith(".py"):
                    files.append(value)
        return files

    async def _run_format(self, files: List[str]) -> QualityGateResult:
        """运行代码格式化"""
        try:
            cmd = f"{self.format_command} {' '.join(files)}"
            result = await self._run_command(cmd)

            return QualityGateResult(
                passed=result["returncode"] == 0,
                gate_name="format",
                message="Code formatted"
                if result["returncode"] == 0
                else "Format failed",
                output=result["stdout"],
                error=result["stderr"],
            )
        except Exception as e:
            return QualityGateResult(
                passed=False,
                gate_name="format",
                message="Format command failed",
                error=str(e),
            )

    async def _run_lint(self, files: List[str]) -> QualityGateResult:
        """运行静态检查"""
        try:
            cmd = f"{self.lint_command} {' '.join(files)}"
            result = await self._run_command(cmd)

            return QualityGateResult(
                passed=result["returncode"] == 0,
                gate_name="lint",
                message="Lint passed"
                if result["returncode"] == 0
                else "Lint errors found",
                output=result["stdout"],
                error=result["stderr"] if result["returncode"] != 0 else "",
            )
        except Exception as e:
            return QualityGateResult(
                passed=False,
                gate_name="lint",
                message="Lint command failed",
                error=str(e),
            )

    async def _run_tests(self) -> QualityGateResult:
        """运行单元测试"""
        try:
            result = await self._run_command(self.test_command)

            return QualityGateResult(
                passed=result["returncode"] == 0,
                gate_name="test",
                message="Tests passed" if result["returncode"] == 0 else "Tests failed",
                output=result["stdout"][-2000:],  # 限制输出长度
                error=result["stderr"][-1000:] if result["returncode"] != 0 else "",
            )
        except Exception as e:
            return QualityGateResult(
                passed=False,
                gate_name="test",
                message="Test command failed",
                error=str(e),
            )

    async def _run_command(self, cmd: str, timeout: int = 120) -> Dict[str, Any]:
        """执行命令"""
        try:
            process = await asyncio.create_subprocess_shell(
                cmd,
                cwd=str(self.working_dir),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await asyncio.wait_for(
                process.communicate(), timeout=timeout
            )

            return {
                "returncode": process.returncode,
                "stdout": stdout.decode() if stdout else "",
                "stderr": stderr.decode() if stderr else "",
            }
        except asyncio.TimeoutError:
            return {
                "returncode": -1,
                "stdout": "",
                "stderr": f"Command timed out after {timeout}s",
            }


# 导出
__all__ = ["PostToolUseHook", "QualityGateResult"]
