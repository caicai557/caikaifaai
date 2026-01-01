"""
CodeReviewSkill - 代码审查技能

组合工具实现自动化代码审查:
1. 静态分析 (ruff)
2. 安全检查
3. 规则与质量评估
"""

from typing import Dict, Any, List, Optional, Callable
from pydantic import BaseModel, Field
import asyncio
import subprocess
import logging
import os
from .base_skill import BaseSkill
from council.tools.file_system import FileTools
from council.observability.tracer import AgentTracer

logger = logging.getLogger(__name__)


class ReviewInput(BaseModel):
    """代码审查输入"""

    files: List[str] = Field(..., description="待审查文件列表")
    check_security: bool = Field(True, description="是否进行安全检查")
    check_style: bool = Field(True, description="是否进行风格检查")


class ReviewIssue(BaseModel):
    """审查问题"""

    file: str
    line: Optional[int] = None
    severity: str  # "error", "warning", "info"
    category: str  # "lint", "security", "logic", "style"
    message: str
    suggestion: Optional[str] = None


class ReviewOutput(BaseModel):
    """代码审查输出"""

    files_reviewed: int
    total_issues: int
    errors: int
    warnings: int
    issues: List[ReviewIssue]
    summary: str
    passed: bool


class CodeReviewSkill(BaseSkill):
    """
    代码审查技能 (CodeReviewSkill)

    能力:
    - 运行静态分析工具 (ruff)
    - 安全漏洞检测
    - 代码风格检查
    - 规则与质量评估

    Features:
    - 多工具集成
    - 严重性分级
    - 修复建议生成
    - OpenTelemetry 追踪
    """

    # 安全敏感关键词
    SECURITY_PATTERNS = [
        ("password", "硬编码密码"),
        ("secret", "敏感信息暴露"),
        ("api_key", "API 密钥泄露"),
        ("eval(", "危险函数调用"),
        ("exec(", "危险函数调用"),
        ("os.system(", "命令注入风险"),
        ("subprocess.call(", "命令注入风险"),
        ("pickle.loads(", "反序列化漏洞"),
    ]

    def __init__(
        self,
        llm_client=None,
        working_dir: str = ".",
        tracer: Optional[AgentTracer] = None,
        approval_callback: Optional[Callable] = None,
        progress_callback: Optional[Callable] = None,
    ):
        super().__init__(
            name="CodeReviewSkill",
            description="Automated code review with static analysis and security checks",
            llm_client=llm_client,
            approval_callback=approval_callback,
            progress_callback=progress_callback,
        )
        self.working_dir = os.path.abspath(working_dir)
        self.file_tools = FileTools(root_dir=self.working_dir)
        self.tracer = tracer or AgentTracer("code-review-skill")

    async def execute(
        self,
        files: List[str],
        check_security: bool = True,
        check_style: bool = True,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        执行代码审查

        Args:
            files: 待审查文件列表
            check_security: 是否进行安全检查
            check_style: 是否进行风格检查
        """
        # 验证输入
        try:
            input_data = ReviewInput(
                files=files, check_security=check_security, check_style=check_style
            )
        except Exception as e:
            logger.error(f"Input validation failed: {e}")
            raise ValueError(f"Invalid input: {e}")

        with self.tracer.trace_agent_step("CodeReviewSkill", "execute") as span:
            span.set_attribute("files_count", len(input_data.files))

            logger.info(
                f"🔍 [CodeReviewSkill] 开始审查 {len(input_data.files)} 个文件..."
            )

            all_issues: List[ReviewIssue] = []

            try:
                # 1. 静态分析 (ruff)
                if input_data.check_style:
                    with self.tracer.trace_tool_call(
                        "ruff", {"files": input_data.files}
                    ):
                        lint_issues = await self._run_ruff(input_data.files)
                        all_issues.extend(lint_issues)
                        logger.info(
                            f"📋 [CodeReviewSkill] Lint 检查发现 {len(lint_issues)} 个问题"
                        )

                # 2. 安全检查
                if input_data.check_security:
                    with self.tracer.trace_tool_call(
                        "security_scan", {"files": input_data.files}
                    ):
                        security_issues = await self._security_scan(input_data.files)
                        all_issues.extend(security_issues)
                        logger.info(
                            f"🔒 [CodeReviewSkill] 安全扫描发现 {len(security_issues)} 个问题"
                        )

                # 3. 统计
                errors = sum(1 for i in all_issues if i.severity == "error")
                warnings = sum(1 for i in all_issues if i.severity == "warning")
                passed = errors == 0

                # 4. 构造输出
                output = ReviewOutput(
                    files_reviewed=len(input_data.files),
                    total_issues=len(all_issues),
                    errors=errors,
                    warnings=warnings,
                    issues=all_issues,
                    summary=f"审查了 {len(input_data.files)} 个文件, 发现 {errors} 个错误, {warnings} 个警告",
                    passed=passed,
                )

                return output.model_dump()

            except Exception as e:
                logger.error(f"Code review failed: {e}", exc_info=True)
                span.set_attribute("error", str(e))
                raise RuntimeError(f"Code review failed: {e}")

    async def _run_ruff(self, files: List[str]) -> List[ReviewIssue]:
        """运行 ruff 静态分析"""
        issues = []

        try:
            cmd = ["ruff", "check", "--output-format=json"] + files
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

            if result.stdout:
                import json

                try:
                    ruff_issues = json.loads(result.stdout)
                    for item in ruff_issues:
                        issues.append(
                            ReviewIssue(
                                file=item.get("filename", "unknown"),
                                line=item.get("location", {}).get("row"),
                                severity="warning"
                                if item.get("code", "").startswith("W")
                                else "error",
                                category="lint",
                                message=f"[{item.get('code')}] {item.get('message', '')}",
                                suggestion=item.get("fix", {}).get("message")
                                if item.get("fix")
                                else None,
                            )
                        )
                except json.JSONDecodeError:
                    pass

        except FileNotFoundError:
            logger.warning("ruff not found, skipping lint check")
        except Exception as e:
            logger.warning(f"ruff failed: {e}")

        return issues

    async def _security_scan(self, files: List[str]) -> List[ReviewIssue]:
        """安全扫描"""
        issues = []

        for file_path in files:
            content = self.file_tools.read_file(file_path)
            if content.startswith("Error"):
                continue

            lines = content.split("\n")
            for line_num, line in enumerate(lines, 1):
                line_lower = line.lower()

                for pattern, description in self.SECURITY_PATTERNS:
                    if pattern in line_lower:
                        issues.append(
                            ReviewIssue(
                                file=file_path,
                                line=line_num,
                                severity="error",
                                category="security",
                                message=f"安全风险: {description}",
                                suggestion="考虑使用环境变量或配置文件管理敏感信息",
                            )
                        )

        return issues
