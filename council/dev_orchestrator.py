"""
DevOrchestrator - 开发编排器

Council 1.0.0 核心入口类，整合所有能力：
- 5模型智能路由 (TaskClassifier)
- Wald 共识决策 (WaldConsensus)
- 自愈循环 (SelfHealingLoop)
- 治理网关 (GovernanceGateway)

使用方法:
    orchestrator = DevOrchestrator()
    result = await orchestrator.dev("实现用户认证模块")
"""

from dataclasses import dataclass, field
from typing import List, Optional, Any, Dict
from datetime import datetime
from enum import Enum
import asyncio

# 内部模块
from council.orchestration.task_classifier import (
    TaskClassifier,
    ClassificationResult,
    RecommendedModel,
)
from council.orchestration.multi_model_executor import (
    MultiModelExecutor,
    ModelTask,
    ModelRole,
)
from council.facilitator.wald_consensus import (
    WaldConsensus,
    WaldConfig,
    ConsensusResult,
    ConsensusDecision,
)
from council.self_healing.loop import (
    SelfHealingLoop,
    HealingReport,
    HealingStatus,
)

# 2025 改进: 专业化 Agent 集成
from council.agents.orchestrator import Orchestrator
from council.agents.architect import Architect
from council.agents.coder import Coder
from council.agents.security_auditor import SecurityAuditor
from council.agents.web_surfer import WebSurfer
from council.core.llm_client import LLMClient, default_client


class DevStatus(Enum):
    """开发状态"""

    ANALYZING = "analyzing"  # 分析任务
    PLANNING = "planning"  # 规划子任务
    EXECUTING = "executing"  # 执行中
    HEALING = "healing"  # 自愈修复中
    REVIEWING = "reviewing"  # 共识审查中
    COMPLETED = "completed"  # 完成
    FAILED = "failed"  # 失败
    HUMAN_REQUIRED = "human_required"  # 需人工介入


@dataclass
class SubTask:
    """子任务"""

    id: str
    description: str
    model: RecommendedModel
    assigned_agent: str = "Coder"  # 2025: 分配的专业 Agent
    status: str = "pending"
    result: Optional[str] = None
    error: Optional[str] = None


@dataclass
class DevResult:
    """开发结果"""

    status: DevStatus
    task: str
    subtasks: List[SubTask] = field(default_factory=list)
    consensus: Optional[ConsensusResult] = None
    healing_report: Optional[HealingReport] = None
    artifacts: List[str] = field(default_factory=list)
    duration_ms: float = 0.0
    message: str = ""
    timestamp: datetime = field(default_factory=datetime.now)


class DevOrchestrator:
    """
    开发编排器 - Council 1.0.0 核心

    整合所有能力的统一入口：
    - 任务分类 → 自动选择最优模型组合
    - 编排分发 → 拆解为可并发的子任务
    - 共识决策 → Wald SPRT 动态判断
    - 自愈循环 → 自动修复测试失败
    - 治理网关 → 高风险操作阻断

    使用:
        orchestrator = DevOrchestrator()
        result = await orchestrator.dev("重构 auth 模块")
    """

    def __init__(
        self,
        working_dir: str = ".",
        test_command: str = "python -m pytest tests/ -v",
        max_healing_iterations: int = 5,
        cost_sensitive: bool = True,
        llm_client: Optional[LLMClient] = None,
        verbose: bool = True,
    ):
        """
        初始化编排器

        Args:
            working_dir: 工作目录
            test_command: 测试命令
            max_healing_iterations: 自愈最大迭代次数
            cost_sensitive: 是否成本敏感（优先用便宜模型）
            llm_fn: LLM 调用函数 (prompt, model) -> response
            verbose: 输出详细日志
        """
        self.working_dir = working_dir
        self.test_command = test_command
        self.max_healing_iterations = max_healing_iterations
        self.verbose = verbose
        # 2025 Core Upgrade: 使用真实的 LLMClient
        self.llm_client = llm_client or default_client

        # 初始化子模块
        self.classifier = TaskClassifier(cost_sensitive=cost_sensitive)
        self.consensus = WaldConsensus(
            WaldConfig(
                upper_limit=0.95,
                lower_limit=0.30,
                prior_approve=0.70,
            )
        )
        self.healing_loop = SelfHealingLoop(
            test_command=test_command,
            max_iterations=max_healing_iterations,
            working_dir=working_dir,
        )

        # 2025 改进: 专业化 Agent 实例
        # 注入 LLMClient 到 Agents
        self.orchestrator_agent = Orchestrator(llm_client=self.llm_client)
        self.agents = {
            "Architect": Architect(llm_client=self.llm_client),
            "Coder": Coder(llm_client=self.llm_client),
            "SecurityAuditor": SecurityAuditor(llm_client=self.llm_client),
            "WebSurfer": WebSurfer(llm_client=self.llm_client),
        }

        # 2026 改进: 多模型并行执行器
        self.multi_executor = MultiModelExecutor(
            llm_client=self.llm_client,
            max_concurrent=3,
            default_timeout=60.0,
            retry_count=1,
        )

        # 模型映射：Agent 名称 -> 推荐模型
        self.agent_model_mapping = {
            "Architect": "claude-sonnet-4-20250514",
            "Coder": "vertex_ai/gemini-2.0-flash",
            "SecurityAuditor": "claude-sonnet-4-20250514",
            "WebSurfer": "gpt-4o-mini",
        }

        # 状态跟踪
        self._current_status = DevStatus.ANALYZING
        self._start_time: Optional[datetime] = None

    async def dev(self, task: str) -> DevResult:
        """
        执行开发任务

        一条命令，调动全部能力：
        1. 任务分类 → 选择模型组合
        2. 编排分发 → 拆解子任务
        3. 并发执行 → 多模型协作
        4. Wald 共识 → 决定下一步
        5. 自愈循环 → 达到 π≥0.95

        Args:
            task: 任务描述

        Returns:
            DevResult: 开发结果
        """
        self._start_time = datetime.now()
        self._log(f"🎯 开始任务: {task}")

        try:
            # 1. 分析任务
            self._update_status(DevStatus.ANALYZING)
            classification = self.classifier.classify(task)
            self._log(f"📊 任务类型: {classification.task_type.value}")
            self._log(f"🤖 主模型: {classification.recommended_model.value}")

            # 2. 规划子任务
            self._update_status(DevStatus.PLANNING)
            subtasks = await self._plan_subtasks(task, classification)
            self._log(f"📋 拆解为 {len(subtasks)} 个子任务")

            # 3. 执行子任务 (2026: 并行执行)
            self._update_status(DevStatus.EXECUTING)
            self._log(f"🚀 并行执行 {len(subtasks)} 个子任务")
            await self._execute_subtasks_parallel(subtasks)

            # 4. 运行测试 + 自愈
            self._update_status(DevStatus.HEALING)
            healing_report = self.healing_loop.run()
            self._log(f"🔧 自愈状态: {healing_report.status.value}")

            # 5. 共识评估 (2026: Wald 实时早停)
            self._update_status(DevStatus.REVIEWING)
            votes = self._collect_votes(subtasks, healing_report)
            
            # 使用实时早停评估 - 每票后检查π是否达标
            consensus_result = None
            for i, vote in enumerate(votes):
                if consensus_result is None:
                    consensus_result = self.consensus.evaluate_realtime(
                        vote, total_expected_votes=len(votes)
                    )
                else:
                    consensus_result = self.consensus.evaluate_realtime(
                        vote, current_state=consensus_result, total_expected_votes=len(votes)
                    )
                
                # 早停检查 - π达标立即返回
                if consensus_result.early_stopped:
                    self._log(f"⚡ 早停! {consensus_result.reason}")
                    break
            
            self._log(f"📊 共识概率 π={consensus_result.pi_approve:.3f} (Token节省: {consensus_result.tokens_saved})")

            # 6. 决策
            if consensus_result.decision == ConsensusDecision.AUTO_COMMIT:
                self._update_status(DevStatus.COMPLETED)
                # 2025 P1: Git 自动提交
                commit_result = self._git_commit(task)
                if commit_result:
                    message = f"✅ 完成并已提交! π={consensus_result.pi_approve:.3f}"
                else:
                    message = (
                        f"✅ 完成! π={consensus_result.pi_approve:.3f} (Git 提交跳过)"
                    )
            elif consensus_result.decision == ConsensusDecision.REJECT:
                self._update_status(DevStatus.FAILED)
                message = f"❌ 失败. {consensus_result.reason}"
            else:
                self._update_status(DevStatus.HUMAN_REQUIRED)
                message = f"⚠️ 需要人工介入. {consensus_result.reason}"

            duration = (datetime.now() - self._start_time).total_seconds() * 1000

            return DevResult(
                status=self._current_status,
                task=task,
                subtasks=subtasks,
                consensus=consensus_result,
                healing_report=healing_report,
                duration_ms=duration,
                message=message,
            )

        except Exception as e:
            self._update_status(DevStatus.FAILED)
            return DevResult(
                status=DevStatus.FAILED,
                task=task,
                message=f"❌ 错误: {str(e)}",
            )

    async def _plan_subtasks(
        self, task: str, classification: ClassificationResult
    ) -> List[SubTask]:
        """规划子任务 - 使用 Orchestrator 结构化拆解"""
        # 2025 改进: 使用 Orchestrator Agent 进行智能拆解
        decomposition = self.orchestrator_agent.decompose(task)

        subtasks = []
        for orch_subtask in decomposition.subtasks:
            subtasks.append(
                SubTask(
                    id=orch_subtask.id,
                    description=orch_subtask.description,
                    model=classification.recommended_model,
                    # 新增: 记录分配的 Agent
                    assigned_agent=getattr(orch_subtask, "assigned_agent", "Coder"),
                )
            )

        self._log(f"📋 Orchestrator 拆解为 {len(subtasks)} 个子任务")
        for st in subtasks:
            self._log(f"   → {st.assigned_agent}: {st.description[:40]}...")

        return subtasks

    async def _execute_subtasks_parallel(self, subtasks: List[SubTask]) -> None:
        """
        并行执行多个子任务 (2026 改进)

        使用 MultiModelExecutor 实现真正的并行执行。
        """
        if not subtasks:
            return

        # 构建 ModelTask 列表
        model_tasks = []
        for subtask in subtasks:
            agent_name = getattr(subtask, "assigned_agent", "Coder")
            model = self.agent_model_mapping.get(
                agent_name, "vertex_ai/gemini-2.0-flash"
            )

            # 确定角色
            role_mapping = {
                "Architect": ModelRole.PLANNER,
                "Coder": ModelRole.EXECUTOR,
                "SecurityAuditor": ModelRole.REVIEWER,
                "WebSurfer": ModelRole.GENERAL,
            }
            role = role_mapping.get(agent_name, ModelRole.EXECUTOR)

            model_tasks.append(
                ModelTask(
                    model=model,
                    prompt=subtask.description,
                    role=role,
                    timeout=60.0,
                    metadata={"subtask_id": subtask.id, "agent": agent_name},
                )
            )

        # 并行执行
        results = await self.multi_executor.execute_parallel(model_tasks)

        # 将结果映射回子任务
        for subtask, result in zip(subtasks, results):
            if result.success:
                subtask.status = "done"
                subtask.result = result.output
                self._log(
                    f"✅ [{subtask.assigned_agent}] 完成 ({result.latency_ms:.0f}ms)"
                )
            else:
                subtask.status = "failed"
                subtask.error = result.error or "执行失败"
                self._log(f"❌ [{subtask.assigned_agent}] 失败: {result.error}")

        # 记录统计信息
        stats = self.multi_executor.get_stats()
        self._log(
            f"📊 并行执行统计: "
            f"成功率={stats.success_rate:.1%}, "
            f"平均延迟={stats.avg_latency_ms:.0f}ms"
        )

    async def _execute_subtask(self, subtask: SubTask) -> Optional[str]:
        """执行单个子任务 - 2025: 使用专业化 Agent (保留用于单任务场景)"""
        agent_name = getattr(subtask, "assigned_agent", "Coder")
        agent = self.agents.get(agent_name)

        if agent is None:
            self._log(f"⚠️ 未知 Agent: {agent_name}, 降级到 Coder")
            agent = self.agents["Coder"]

        self._log(f"🤖 {agent_name} 执行: {subtask.description[:40]}...")

        try:
            # 调用 Agent 的 execute 方法
            exec_result = agent.execute(subtask.description)

            if exec_result.success:
                return exec_result.output
            else:
                subtask.error = (
                    "; ".join(exec_result.errors) if exec_result.errors else "执行失败"
                )
                return exec_result.output  # 仍返回输出以便调试
        except Exception as e:
            subtask.error = str(e)
            self._log(f"❌ {agent_name} 执行失败: {e}")
            return None

    def _collect_votes(
        self, subtasks: List[SubTask], healing_report: HealingReport
    ) -> List[Dict[str, Any]]:
        """收集投票用于共识"""
        votes = []

        # 子任务完成度投票
        completed = sum(1 for s in subtasks if s.status == "done")
        total = len(subtasks)
        task_confidence = completed / total if total > 0 else 0
        votes.append(
            {
                "agent": "TaskExecutor",
                "decision": "approve" if task_confidence > 0.8 else "hold",
                "confidence": task_confidence,
                "rationale": f"完成 {completed}/{total} 子任务",
            }
        )

        # 测试结果投票
        if healing_report.status == HealingStatus.SUCCESS:
            votes.append(
                {
                    "agent": "TestRunner",
                    "decision": "approve",
                    "confidence": 0.95,
                    "rationale": "所有测试通过",
                }
            )
        elif healing_report.status == HealingStatus.PARTIAL:
            votes.append(
                {
                    "agent": "TestRunner",
                    "decision": "approve_with_changes",
                    "confidence": 0.7,
                    "rationale": f"部分测试通过 ({healing_report.final_failures} 失败)",
                }
            )
        else:
            votes.append(
                {
                    "agent": "TestRunner",
                    "decision": "reject",
                    "confidence": 0.9,
                    "rationale": f"测试失败 ({healing_report.final_failures} 失败)",
                }
            )

        # 自愈效果投票
        if healing_report.initial_failures > healing_report.final_failures:
            improvement = (
                healing_report.initial_failures - healing_report.final_failures
            ) / max(healing_report.initial_failures, 1)
            votes.append(
                {
                    "agent": "SelfHealer",
                    "decision": "approve_with_changes",
                    "confidence": improvement,
                    "rationale": f"修复了 {healing_report.initial_failures - healing_report.final_failures} 个失败",
                }
            )

        # 2025 改进: 收集 SecurityAuditor 独立审核投票
        security_agent = self.agents.get("SecurityAuditor")
        if security_agent:
            try:
                # 使用 SecurityAuditor 的 vote 方法审核整体变更
                completed_tasks = [s for s in subtasks if s.status == "done"]
                if completed_tasks:
                    changes_summary = "\n".join(
                        [s.description for s in completed_tasks[:3]]
                    )
                    security_vote = security_agent.vote(
                        f"审核以下代码变更的安全性:\n{changes_summary}"
                    )
                    votes.append(
                        {
                            "agent": "SecurityAuditor",
                            "decision": security_vote.decision.value,
                            "confidence": security_vote.confidence,
                            "rationale": security_vote.rationale[:100],
                        }
                    )
            except Exception:
                pass  # 静默失败，不阻塞主流程

        return votes

    async def _default_llm(self, prompt: str, model: str) -> str:
        """默认 LLM 调用 (模拟)"""
        # 在实际使用中，这里会调用真实的 LLM API
        await asyncio.sleep(0.1)

        if "拆解" in prompt or "子任务" in prompt:
            return """
1. 分析现有代码结构
2. 设计新的接口
3. 实现核心逻辑
4. 编写单元测试
"""
        else:
            return f"# 执行: {prompt[:50]}...\n# [模拟代码生成]"

    def _update_status(self, status: DevStatus):
        """更新状态"""
        self._current_status = status
        self._log(f"📍 状态: {status.value}")

    def _log(self, msg: str):
        """输出日志"""
        if self.verbose:
            ts = datetime.now().strftime("%H:%M:%S")
            print(f"[{ts}] DevOrchestrator: {msg}")

    def _git_commit(self, task: str) -> bool:
        """2025 P1: Git 自动提交"""
        import subprocess

        try:
            # Stage all changes
            subprocess.run(
                ["git", "add", "-A"],
                cwd=self.working_dir,
                capture_output=True,
                check=True,
            )
            # Commit with task description
            commit_msg = f"[council] {task[:50]}"
            result = subprocess.run(
                ["git", "commit", "-m", commit_msg],
                cwd=self.working_dir,
                capture_output=True,
            )
            if result.returncode == 0:
                self._log(f"📝 Git commit: {commit_msg}")
                return True
            else:
                self._log("⚠️ Git commit 跳过 (无变更或失败)")
                return False
        except Exception as e:
            self._log(f"⚠️ Git 不可用: {e}")
            return False


# 导出
__all__ = [
    "DevOrchestrator",
    "DevResult",
    "DevStatus",
    "SubTask",
]
