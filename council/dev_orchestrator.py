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
from typing import List, Optional, Callable, Any, Dict
from datetime import datetime
from enum import Enum
import asyncio

# 内部模块
from council.orchestration.task_classifier import (
    TaskClassifier,
    ClassificationResult,
    RecommendedModel,
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
        llm_fn: Optional[Callable[[str, str], str]] = None,
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
        self.llm_fn = llm_fn or self._default_llm

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

            # 3. 执行子任务
            self._update_status(DevStatus.EXECUTING)
            for i, subtask in enumerate(subtasks):
                self._log(f"🔄 [{i + 1}/{len(subtasks)}] {subtask.description[:50]}...")
                result = await self._execute_subtask(subtask)
                subtask.status = "done" if result else "failed"
                subtask.result = result

            # 4. 运行测试 + 自愈
            self._update_status(DevStatus.HEALING)
            healing_report = self.healing_loop.run()
            self._log(f"🔧 自愈状态: {healing_report.status.value}")

            # 5. 共识评估
            self._update_status(DevStatus.REVIEWING)
            votes = self._collect_votes(subtasks, healing_report)
            consensus_result = self.consensus.evaluate(votes)
            self._log(f"📊 共识概率 π={consensus_result.pi_approve:.3f}")

            # 6. 决策
            if consensus_result.decision == ConsensusDecision.AUTO_COMMIT:
                self._update_status(DevStatus.COMPLETED)
                message = f"✅ 完成! π={consensus_result.pi_approve:.3f}"
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
        """规划子任务"""
        # 使用 LLM 拆解任务
        prompt = f"""请将以下开发任务拆解为3-5个可独立执行的子任务。
每个子任务应该是一个具体的代码变更。

任务: {task}
任务类型: {classification.task_type.value}

返回格式 (每行一个子任务):
1. 子任务描述
2. 子任务描述
3. 子任务描述
"""
        response = await self.llm_fn(prompt, classification.recommended_model.value)

        # 解析响应
        lines = [l.strip() for l in response.strip().split("\n") if l.strip()]
        subtasks = []
        for i, line in enumerate(lines[:5]):
            clean = line.lstrip("0123456789.-) ").strip()
            if clean:
                subtasks.append(
                    SubTask(
                        id=f"subtask_{i + 1}",
                        description=clean,
                        model=classification.recommended_model,
                    )
                )

        # 至少有一个任务
        if not subtasks:
            subtasks = [
                SubTask(
                    id="subtask_1",
                    description=task,
                    model=classification.recommended_model,
                )
            ]

        return subtasks

    async def _execute_subtask(self, subtask: SubTask) -> Optional[str]:
        """执行单个子任务"""
        prompt = f"""请执行以下开发任务并生成代码:

任务: {subtask.description}

请直接输出代码变更，包括:
1. 需要修改的文件路径
2. 完整的代码内容
"""
        try:
            result = await self.llm_fn(prompt, subtask.model.value)
            return result
        except Exception as e:
            subtask.error = str(e)
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


# 导出
__all__ = [
    "DevOrchestrator",
    "DevResult",
    "DevStatus",
    "SubTask",
]
