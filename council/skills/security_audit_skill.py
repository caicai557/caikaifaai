"""
SecurityAuditSkill - 安全审计技能

组合工具实现自动化安全审计:
1. 敏感路径扫描
2. 依赖漏洞检查
3. 权限边界分析
4. 审计报告生成
"""

from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
import asyncio
import subprocess
import logging
import os
import re
from .base_skill import BaseSkill, ApprovalCallback, ProgressCallback
from council.tools.file_system import FileTools
from council.observability.tracer import AgentTracer

logger = logging.getLogger(__name__)


class AuditInput(BaseModel):
    """安全审计输入"""

    target_dir: str = Field(".", description="审计目标目录")
    check_dependencies: bool = Field(True, description="是否检查依赖漏洞")
    check_secrets: bool = Field(True, description="是否检查敏感信息泄露")


class SecurityFinding(BaseModel):
    """安全发现"""

    severity: str  # "critical", "high", "medium", "low"
    category: str  # "secret", "dependency", "permission", "config"
    title: str
    description: str
    file: Optional[str] = None
    line: Optional[int] = None
    recommendation: str


class AuditOutput(BaseModel):
    """安全审计输出"""

    target: str
    findings_count: int
    critical_count: int
    high_count: int
    findings: List[SecurityFinding]
    passed: bool
    summary: str


class SecurityAuditSkill(BaseSkill):
    """
    安全审计技能 (SecurityAuditSkill)

    能力:
    - 敏感信息泄露检测 (API Key, Password, Token)
    - 敏感路径访问检查 (.ssh, .env, secrets/)
    - 依赖漏洞扫描 (pip-audit)
    - 审计报告生成

    Features:
    - 正则表达式模式匹配
    - 严重性分级
    - 修复建议
    - OpenTelemetry 追踪
    - HITL: 发现 Critical 问题时请求确认
    - Streaming: 实时汇报扫描进度
    """

    # 敏感信息模式
    SECRET_PATTERNS = [
        (
            r"(?i)(api[_-]?key|apikey)\s*[=:]\s*['\"][^'\"]{10,}['\"]",
            "API Key 泄露",
            "critical",
        ),
        (
            r"(?i)(password|passwd|pwd)\s*[=:]\s*['\"][^'\"]+['\"]",
            "密码硬编码",
            "critical",
        ),
        (
            r"(?i)(secret[_-]?key|secretkey)\s*[=:]\s*['\"][^'\"]{10,}['\"]",
            "Secret Key 泄露",
            "critical",
        ),
        (
            r"(?i)(access[_-]?token|accesstoken)\s*[=:]\s*['\"][^'\"]+['\"]",
            "Access Token 泄露",
            "high",
        ),
        (
            r"(?i)(private[_-]?key)\s*[=:]\s*['\"][^'\"]+['\"]",
            "Private Key 泄露",
            "critical",
        ),
        (r"(?i)Bearer\s+[a-zA-Z0-9\-_\.]+", "Bearer Token 泄露", "high"),
        (r"ghp_[a-zA-Z0-9]{36}", "GitHub Personal Access Token", "critical"),
        (r"sk-[a-zA-Z0-9]{48}", "OpenAI API Key", "critical"),
    ]

    # 敏感路径
    SENSITIVE_PATHS = [
        ".ssh/",
        ".env",
        "secrets/",
        ".aws/",
        ".npmrc",
        ".pypirc",
        "id_rsa",
        "id_ed25519",
    ]

    def __init__(
        self,
        llm_client=None,
        working_dir: str = ".",
        tracer: Optional[AgentTracer] = None,
        approval_callback: Optional[ApprovalCallback] = None,
        progress_callback: Optional[ProgressCallback] = None,
    ):
        super().__init__(
            name="SecurityAuditSkill",
            description="Automated security audit with secret detection and vulnerability scanning",
            llm_client=llm_client,
            approval_callback=approval_callback,
            progress_callback=progress_callback,
        )
        self.working_dir = os.path.abspath(working_dir)
        self.file_tools = FileTools(root_dir=self.working_dir)
        self.tracer = tracer or AgentTracer("security-audit-skill")

    async def execute(
        self,
        target_dir: str = ".",
        check_dependencies: bool = True,
        check_secrets: bool = True,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        执行安全审计

        Args:
            target_dir: 审计目标目录
            check_dependencies: 是否检查依赖漏洞
            check_secrets: 是否检查敏感信息泄露
        """
        try:
            input_data = AuditInput(
                target_dir=target_dir,
                check_dependencies=check_dependencies,
                check_secrets=check_secrets,
            )

            # 安全检查: 防止路径遍历
            safe_target = os.path.abspath(
                os.path.join(self.working_dir, input_data.target_dir)
            )
            if not safe_target.startswith(self.working_dir):
                raise ValueError(
                    f"Target directory '{input_data.target_dir}' is outside working directory '{self.working_dir}'"
                )

            # 更新 input_data 为安全路径 (相对于 working_dir 的路径，或者直接使用 safe_target 但需注意后续 os.walk 的拼接)
            # 原代码使用 os.path.join(self.working_dir, target_dir)，如果 target_dir 是绝对路径会忽略 working_dir
            # 这里我们确保传递给后续方法的 target_dir 是安全的相对路径
            input_data.target_dir = os.path.relpath(safe_target, self.working_dir)
        except Exception as e:
            logger.error(f"Input validation failed: {e}")
            raise ValueError(f"Invalid input: {e}")

        with self.tracer.trace_agent_step("SecurityAuditSkill", "execute") as span:
            span.set_attribute("target", input_data.target_dir)

            logger.info(
                f"🔐 [SecurityAuditSkill] 开始安全审计: {input_data.target_dir}"
            )
            await self.report_progress("开始安全审计...", 0, 100)

            all_findings: List[SecurityFinding] = []

            try:
                # 1. 敏感信息扫描
                if input_data.check_secrets:
                    await self.report_progress("正在扫描敏感信息...", 20, 100)
                    with self.tracer.trace_tool_call(
                        "secret_scan", {"target": input_data.target_dir}
                    ):
                        secret_findings = await self._scan_secrets(
                            input_data.target_dir
                        )
                        all_findings.extend(secret_findings)
                        logger.info(
                            f"🔍 [SecurityAuditSkill] 敏感信息扫描发现 {len(secret_findings)} 个问题"
                        )

                # 2. 敏感路径检查
                await self.report_progress("正在检查敏感路径...", 50, 100)
                with self.tracer.trace_tool_call(
                    "path_check", {"target": input_data.target_dir}
                ):
                    path_findings = await self._check_sensitive_paths(
                        input_data.target_dir
                    )
                    all_findings.extend(path_findings)
                    logger.info(
                        f"📁 [SecurityAuditSkill] 敏感路径检查发现 {len(path_findings)} 个问题"
                    )

                # 3. 依赖漏洞检查
                if input_data.check_dependencies:
                    await self.report_progress("正在检查依赖漏洞...", 70, 100)
                    with self.tracer.trace_tool_call("dependency_check", {}):
                        dep_findings = await self._check_dependencies()
                        all_findings.extend(dep_findings)
                        logger.info(
                            f"📦 [SecurityAuditSkill] 依赖检查发现 {len(dep_findings)} 个问题"
                        )

                # 4. 统计与 HITL
                critical = sum(1 for f in all_findings if f.severity == "critical")
                high = sum(1 for f in all_findings if f.severity == "high")

                if critical > 0:
                    await self.report_progress(
                        f"发现 {critical} 个严重问题，请求确认...", 90, 100
                    )
                    approved = await self.request_approval(
                        "critical_findings_found",
                        {
                            "count": critical,
                            "findings": [
                                f.model_dump()
                                for f in all_findings
                                if f.severity == "critical"
                            ],
                        },
                    )
                    if not approved:
                        logger.warning("用户中止了审计流程")
                        # 可以选择抛出异常或返回特定状态，这里我们继续但标记

                passed = critical == 0

                output = AuditOutput(
                    target=input_data.target_dir,
                    findings_count=len(all_findings),
                    critical_count=critical,
                    high_count=high,
                    findings=all_findings,
                    passed=passed,
                    summary=f"审计发现 {critical} 个严重问题, {high} 个高危问题",
                )

                await self.report_progress("审计完成", 100, 100)
                return output.model_dump()

            except Exception as e:
                logger.error(f"Security audit failed: {e}", exc_info=True)
                span.set_attribute("error", str(e))
                raise RuntimeError(f"Security audit failed: {e}")

    async def _scan_secrets(self, target_dir: str) -> List[SecurityFinding]:
        """扫描敏感信息"""
        findings = []

        # 获取所有 Python 文件
        for root, dirs, files in os.walk(os.path.join(self.working_dir, target_dir)):
            # 跳过隐藏目录和虚拟环境
            dirs[:] = [
                d
                for d in dirs
                if not d.startswith(".")
                and d != "__pycache__"
                and d != "venv"
                and d != ".venv"
            ]

            for file in files:
                if file.endswith(
                    (
                        ".py",
                        ".js",
                        ".ts",
                        ".json",
                        ".yaml",
                        ".yml",
                        ".env",
                        ".cfg",
                        ".ini",
                    )
                ):
                    file_path = os.path.join(root, file)
                    rel_path = os.path.relpath(file_path, self.working_dir)

                    try:
                        with open(
                            file_path, "r", encoding="utf-8", errors="ignore"
                        ) as f:
                            content = f.read()

                        for pattern, title, severity in self.SECRET_PATTERNS:
                            for match in re.finditer(pattern, content):
                                line_num = content[: match.start()].count("\n") + 1
                                findings.append(
                                    SecurityFinding(
                                        severity=severity,
                                        category="secret",
                                        title=title,
                                        description=f"检测到可能的敏感信息: {match.group()[:30]}...",
                                        file=rel_path,
                                        line=line_num,
                                        recommendation="使用环境变量或密钥管理服务存储敏感信息",
                                    )
                                )
                    except Exception:
                        pass

        return findings

    async def _check_sensitive_paths(self, target_dir: str) -> List[SecurityFinding]:
        """检查敏感路径"""
        findings = []

        for root, dirs, files in os.walk(os.path.join(self.working_dir, target_dir)):
            for file in files:
                file_path = os.path.join(root, file)
                rel_path = os.path.relpath(file_path, self.working_dir)

                for pattern in self.SENSITIVE_PATHS:
                    if pattern in rel_path:
                        findings.append(
                            SecurityFinding(
                                severity="high",
                                category="permission",
                                title=f"敏感路径访问: {pattern}",
                                description=f"文件 {rel_path} 可能包含敏感信息",
                                file=rel_path,
                                recommendation="确保敏感文件已添加到 .gitignore 并使用适当的权限",
                            )
                        )

        return findings

    async def _check_dependencies(self) -> List[SecurityFinding]:
        """检查依赖漏洞"""
        findings = []

        # 检查是否存在 requirements.txt 或 pyproject.toml
        req_file = os.path.join(self.working_dir, "requirements.txt")
        pyproject = os.path.join(self.working_dir, "pyproject.toml")

        if not os.path.exists(req_file) and not os.path.exists(pyproject):
            return findings

        try:
            # 尝试运行 pip-audit
            result = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: subprocess.run(
                    ["pip-audit", "--format=json"],
                    cwd=self.working_dir,
                    capture_output=True,
                    text=True,
                    timeout=120,
                ),
            )

            if result.stdout:
                import json

                try:
                    vulns = json.loads(result.stdout)
                    for vuln in vulns.get("dependencies", []):
                        for v in vuln.get("vulns", []):
                            findings.append(
                                SecurityFinding(
                                    severity="high"
                                    if v.get("fix_versions")
                                    else "critical",
                                    category="dependency",
                                    title=f"依赖漏洞: {vuln.get('name')}",
                                    description=f"{v.get('id')}: {v.get('description', '')[:100]}",
                                    recommendation=f"升级到版本 {v.get('fix_versions', ['latest'])[0]}"
                                    if v.get("fix_versions")
                                    else "寻找替代库",
                                )
                            )
                except json.JSONDecodeError:
                    pass

        except FileNotFoundError:
            logger.info("pip-audit not found, skipping dependency check")
        except Exception as e:
            logger.warning(f"Dependency check failed: {e}")

        return findings
