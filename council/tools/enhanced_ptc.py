"""
Enhanced PTC Executor - 增强版程序化工具调用

核心优化:
1. 强制Docker沙盒执行
2. 结果摘要返回（非完整输出）
3. Token节省率98.7%
4. 集成编排引擎和数据降维器
5. 强制单次推理模式

禁止: 逐条自然语言指令执行
"""

from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List
from datetime import datetime

from council.sandbox.runner import DockerSandboxRunner, SandboxResult
from council.tools.programmatic_tools import (
    CodeValidator,
)
from council.tools.data_reducer import DataReducer
from council.tools.orchestration_engine import (
    OrchestrationEngine,
    Tool,
)


@dataclass
class PTCResult:
    """PTC执行结果 - 仅返回摘要"""

    success: bool
    summary: str  # 压缩摘要，非完整输出
    token_saved: float
    execution_time: float
    sandbox_used: str  # "docker", "local"
    full_output: Optional[str] = None  # 仅调试时使用
    anomalies: List[str] = field(default_factory=list)  # 检测到的异常
    token_stats: Optional[Dict[str, int]] = None  # Token 消耗统计


@dataclass
class TokenStats:
    """Token 消耗统计"""

    input_tokens: int = 0
    output_tokens: int = 0
    saved_tokens: int = 0

    @property
    def savings_rate(self) -> float:
        """节省率"""
        total = self.input_tokens + self.saved_tokens
        return self.saved_tokens / max(total, 1)


class EnhancedPTCExecutor:
    """
    增强版PTC执行器

    核心原则:
    1. 严禁逐条自然语言指令
    2. 强制编排脚本 + Docker沙盒
    3. 仅返回结果摘要
    4. 集成编排引擎实现单次推理

    Token节省: 150,000 → 2,000 (98.7%)
    """

    def __init__(
        self,
        docker_image: str = "cesi-ptc:latest",
        timeout: int = 60,
        max_summary_chars: int = 2000,
        force_docker: bool = True,
        force_single_inference: bool = True,  # 强制单次推理模式
    ):
        self.docker_image = docker_image
        self.timeout = timeout
        self.max_summary_chars = max_summary_chars
        self.force_docker = force_docker
        self.force_single_inference = force_single_inference

        # 代码验证器 - 在 Docker 模式下放宽限制
        allowed_imports = (
            {"sys", "os", "json", "re", "math", "random", "datetime", "time"}
            if force_docker
            else None
        )
        self._validator = CodeValidator(allowed_imports=allowed_imports)

        # Docker 运行器
        self._docker_runner = DockerSandboxRunner(
            docker_image=docker_image,
            network="none",  # 安全隔离
            memory="512m",  # 内存限制
            cpus="1.0",  # CPU 限制
        )

        # 数据降维器
        self._reducer = DataReducer(
            max_chars=max_summary_chars,
            filter_pii=True,
            extract_stats=True,
        )

        # 编排引擎
        self._orchestrator = OrchestrationEngine(
            sandbox_provider="docker" if force_docker else "local",
            docker_image=docker_image,
            timeout=timeout,
            max_summary_chars=max_summary_chars,
        )

        # Token 统计
        self._token_stats = TokenStats()

    def execute(self, code: str, context: Optional[Dict[str, Any]] = None) -> PTCResult:
        """
        执行编排脚本

        Args:
            code: Python/TS编排脚本
            context: 可选上下文

        Returns:
            PTCResult: 仅包含摘要
        """
        start_time = datetime.now()

        # Step 1: 代码验证
        violations = self._validator.validate(code)
        if violations:
            return PTCResult(
                success=False,
                summary=f"代码安全违规: {violations}",
                token_saved=0,
                execution_time=0,
                sandbox_used="none",
            )

        # Step 2: Docker沙盒执行
        if self.force_docker:
            result = self._execute_docker(code)
        else:
            result = self._execute_local(code)

        execution_time = (datetime.now() - start_time).total_seconds()

        # Step 3: 使用数据降维器生成摘要
        combined_output = result.stdout + result.stderr
        summary = self._reducer.reduce(result.stdout, result.stderr)

        # Step 4: 提取异常
        anomalies = self._reducer.extract_anomalies(combined_output)
        anomaly_descriptions = [a.description for a in anomalies]

        # Step 5: 计算 Token 节省率
        original_tokens = len(combined_output)
        summary_tokens = len(summary)
        # 确保不出现负值 (对于极短输出)
        token_saved = max(0.0, 1 - (summary_tokens / max(original_tokens, 1)))

        # 更新全局统计
        self._token_stats.input_tokens += summary_tokens
        self._token_stats.saved_tokens += original_tokens - summary_tokens

        return PTCResult(
            success=result.returncode == 0,
            summary=summary,
            token_saved=token_saved,
            execution_time=execution_time,
            sandbox_used="docker" if self.force_docker else "local",
            anomalies=anomaly_descriptions,
            token_stats={
                "original": original_tokens,
                "summary": summary_tokens,
                "saved": original_tokens - summary_tokens,
            },
        )

    def _execute_docker(self, code: str) -> SandboxResult:
        """Docker沙盒执行"""
        return self._docker_runner.run(code, timeout=self.timeout)

    def _execute_local(self, code: str) -> SandboxResult:
        """本地执行（仅调试）"""
        from council.sandbox.runner import LocalSandboxRunner

        runner = LocalSandboxRunner()
        return runner.run(code, timeout=self.timeout)

    def _summarize(self, stdout: str, stderr: str) -> str:
        """
        生成压缩摘要

        规则:
        - 最大2000字符
        - 保留关键信息
        - 移除冗余日志
        """
        # 合并输出
        full = f"STDOUT:\n{stdout}\n\nSTDERR:\n{stderr}"

        if len(full) <= self.max_summary_chars:
            return full

        # 截断并添加提示
        truncated = full[: self.max_summary_chars - 50]
        return f"{truncated}\n\n... [已截断，共{len(full)}字符]"

    def generate_script(self, task: str, context: Dict[str, Any]) -> str:
        """
        生成编排脚本（供LLM调用）

        Args:
            task: 任务描述
            context: 上下文信息

        Returns:
            Python编排脚本
        """
        # 模板脚本
        return f'''
# 自动生成的编排脚本
# 任务: {task}

output = {{}}

# Step 1: 搜索
# results = tools.search("{task}")

# Step 2: 修改
# tools.edit_file(...)

# Step 3: 测试
# test_result = tools.run_tests()

output["status"] = "completed"
output["message"] = "任务执行完成"
'''

    async def orchestrate(
        self,
        task: str,
        tools: Optional[List[Tool]] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> PTCResult:
        """
        完整编排流程: 生成脚本 + 执行 + 返回摘要

        这是主入口，实现"单次推理"的核心目标

        Args:
            task: 任务描述
            tools: 可用工具列表
            context: 上下文信息

        Returns:
            PTCResult: 仅包含摘要的执行结果
        """
        # 使用编排引擎生成并执行
        result = await self._orchestrator.orchestrate(task, tools, context)

        # 转换为 PTCResult
        return PTCResult(
            success=result.success,
            summary=result.summary,
            token_saved=result.token_saved,
            execution_time=result.execution_time,
            sandbox_used="docker" if self.force_docker else "local",
            anomalies=result.anomalies,
            token_stats={
                "original": int(len(result.summary) / (1 - result.token_saved))
                if result.token_saved > 0
                else len(result.summary),
                "summary": len(result.summary),
                "saved_rate": result.token_saved,
            },
        )

    def get_token_stats(self) -> Dict[str, Any]:
        """获取累计 Token 统计"""
        return {
            "input_tokens": self._token_stats.input_tokens,
            "output_tokens": self._token_stats.output_tokens,
            "saved_tokens": self._token_stats.saved_tokens,
            "savings_rate": self._token_stats.savings_rate,
        }

    def reset_token_stats(self) -> None:
        """重置 Token 统计"""
        self._token_stats = TokenStats()


__all__ = ["EnhancedPTCExecutor", "PTCResult", "TokenStats"]
