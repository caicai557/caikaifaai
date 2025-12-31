"""
DevOrchestrator - 开发编排器 (State Machine Edition)

Council 1.0.0 核心入口类，整合所有能力：
- 5模型智能路由 (TaskClassifier)
- Wald 共识决策 (WaldConsensus)
- 自愈循环 (SelfHealingLoop)
- 治理网关 (GovernanceGateway)
- **多智能体协作 (Architect, Coder, Reviewer)**
- **状态机驱动 (CouncilState)**

使用方法:
    orchestrator = DevOrchestrator()
    result = await orchestrator.dev("实现用户认证模块")
"""

from dataclasses import dataclass, field
from typing import List, Optional, Any, Dict
from datetime import datetime
import asyncio
from pathlib import Path

# 内部模块
from council.config import config
from council.orchestration.task_classifier import TaskClassifier
from council.facilitator.wald_consensus import (
    WaldConsensus,
    WaldConfig,
    ConsensusDecision,
)
from council.self_healing.loop import SelfHealingLoop
from council.agents.architect import Architect
from council.agents.coder import Coder
from council.agents.reviewer import Reviewer
from council.protocol.schema import (
    CouncilState,
    DevStatus,
    Plan,
    Subtask,
    MinimalThinkResult,
)


from council.context.rolling_context import RollingContext
from council.observability.logger import logger
from typing import Callable



class DevOrchestrator:
    """
    开发编排器 - Council 1.0.0 核心 (State Machine)
    """

    def __init__(
        self,
        working_dir: str = ".",
        verbose: bool = True,
    ):
        """
        初始化编排器
        """
        self.working_dir = working_dir or config.WORKING_DIR
        self.verbose = verbose or config.VERBOSE

        # 初始化上下文管理器
        self.context = RollingContext(max_tokens=8000)

        # 初始化子模块
        self.classifier = TaskClassifier()
        self.consensus = WaldConsensus(
            WaldConfig(
                upper_limit=config.WALD_UPPER_LIMIT,
                lower_limit=config.WALD_LOWER_LIMIT,
                prior_approve=config.WALD_PRIOR,
            )
        )
        self.healing_loop = SelfHealingLoop(
            test_command=config.TEST_COMMAND,
            max_iterations=config.MAX_HEALING_ITERATIONS,
            working_dir=self.working_dir,
        )

        # 初始化核心智能体
        self.architect = Architect(model=config.PLANNER_MODEL)
        self.coder = Coder(model=config.CODER_MODEL)
        self.reviewer = Reviewer(model=config.REVIEWER_MODEL)

    async def dev(
        self, 
        task: str, 
        stream_handler: Optional[Callable[[str], None]] = None
    ) -> CouncilState:
        """
        执行开发任务 (State Machine Loop)
        
        Args:
            task: 任务描述
            stream_handler: 可选的流式输出回调 (接收 token)
        """
        # 设置流式回调
        if stream_handler:
            self.architect.set_stream_callback(stream_handler)
            self.coder.set_stream_callback(stream_handler)
            self.reviewer.set_stream_callback(stream_handler)

        # 初始化状态
        state = CouncilState(task=task)
        state.log(f"🎯 开始任务: {task}")
        logger.info(f"🎯 开始任务: {task}")
        
        start_time = datetime.now()

        # 状态机循环
        while state.status not in [DevStatus.COMPLETED, DevStatus.FAILED, DevStatus.HUMAN_REQUIRED]:
            current_status = state.status
            state.log(f"📍 进入状态: {current_status.value}")
            
            if self.verbose:
                logger.info(f"State: {current_status.value}")

            try:
                if current_status == DevStatus.EXPLORING:
                    await self._handle_exploring(state)
                elif current_status == DevStatus.ANALYZING:
                    await self._handle_analyzing(state)
                elif current_status == DevStatus.PLANNING:
                    await self._handle_planning(state)
                elif current_status == DevStatus.CODING:
                    await self._handle_coding(state)
                elif current_status == DevStatus.TESTING:
                    await self._handle_testing(state)
                elif current_status == DevStatus.HEALING:
                    await self._handle_healing(state)
                elif current_status == DevStatus.REVIEWING:
                    await self._handle_reviewing(state)
                
            except Exception as e:
                state.status = DevStatus.FAILED
                state.log(f"❌ 发生异常: {str(e)}")
                logger.exception(f"❌ 发生异常: {str(e)}")

        duration = (datetime.now() - start_time).total_seconds()
        state.log(f"🏁 任务结束. 耗时: {duration:.2f}s")
        logger.info(f"🏁 任务结束. 耗时: {duration:.2f}s")
        return state

    async def _handle_exploring(self, state: CouncilState):
        """处理探索阶段 (EPCC: Explore)"""
        state.log("🔍 探索阶段: 理解任务上下文...")
        
        # 加载所有上下文文档 (CLAUDE.md, 工具文档, 代码风格)
        context_docs = self._load_context_docs()
        if context_docs:
            full_context = "\n\n".join([doc for _, doc in context_docs])
            self.context.set_static_context(full_context)
            state.log(f"📄 已加载上下文: {', '.join([name for name, _ in context_docs])}")
        
        # 进入分析阶段
        state.status = DevStatus.ANALYZING

    def _load_context_docs(self) -> List[tuple[str, str]]:
        """加载所有上下文文档"""
        docs = []
        
        # 1. CLAUDE.md 项目上下文
        claude_md_path = Path(self.working_dir) / "CLAUDE.md"
        if claude_md_path.exists():
            try:
                content = claude_md_path.read_text(encoding="utf-8")
                docs.append(("CLAUDE.md", f"Project Context (CLAUDE.md):\n{content}"))
            except Exception:
                pass
        
        # 2. 工具文档 (自动生成)
        from council.mcp import DEFAULT_TOOLS
        tool_docs = "Available Tools:\n"
        for tool in DEFAULT_TOOLS:
            tool_docs += f"- {tool.name}: {tool.description} (Cost: {tool.token_cost})\n"
        docs.append(("Tools", tool_docs))
        
        # 3. 代码风格 (.editorconfig)
        editorconfig_path = Path(self.working_dir) / ".editorconfig"
        if editorconfig_path.exists():
            try:
                content = editorconfig_path.read_text(encoding="utf-8")
                docs.append((".editorconfig", f"Code Style (.editorconfig):\n{content}"))
            except Exception:
                pass
            
        return docs
        
        # 进入分析阶段
        state.status = DevStatus.ANALYZING

    async def _handle_analyzing(self, state: CouncilState):
        """处理分析阶段 - 任务分类与模型路由"""
        classification = self.classifier.classify(state.task)
        
        # 记录完整分类信息
        state.log(f"📊 任务分类: {classification.task_type.value}")
        state.log(f"🤖 推荐模型: {classification.recommended_model.value}")
        state.log(f"📈 置信度: {classification.confidence:.2f}")
        
        # 存储分类结果供后续阶段使用 (扩展 state)
        if not hasattr(state, 'metadata'):
            state.metadata = {}
        state.metadata['task_type'] = classification.task_type.value
        state.metadata['recommended_model'] = classification.recommended_model.value
        state.metadata['classification_confidence'] = classification.confidence
        
        logger.info(f"📊 任务分类: {classification.task_type.value} -> {classification.recommended_model.value}")
        
        state.status = DevStatus.PLANNING

    async def _handle_planning(self, state: CouncilState):
        """处理规划阶段"""
        # 记录用户任务
        self.context.add_turn("User", state.task)

        # Architect 思考
        think_result = self.architect.think_structured(state.task, context={"history": self.context.get_context_for_prompt()})
        state.log(f"🧠 Architect 方案: {think_result.summary}")
        
        # 记录思考结果
        self.context.add_turn("Architect", think_result.summary)
        
        # 创建计划
        subtasks = []
        if think_result.suggestions:
            for i, suggestion in enumerate(think_result.suggestions):
                subtasks.append(Subtask(
                    id=i+1,
                    description=suggestion,
                    status="pending"
                ))
        else:
            subtasks.append(Subtask(id=1, description=state.task))
            
        state.plan = Plan(
            goal=state.task,
            subtasks=subtasks,
            risks=think_result.concerns
        )
        state.status = DevStatus.CODING

    async def _handle_coding(self, state: CouncilState):
        """处理编码阶段"""
        if not state.plan:
            state.status = DevStatus.FAILED
            return

        all_done = True
        for subtask in state.plan.subtasks:
            if subtask.status == "pending":
                state.log(f"🔄 执行子任务: {subtask.description}")
                
                # Coder 执行
                exec_result = self.coder.execute(subtask.description, plan=state.plan.model_dump())
                
                if exec_result.success:
                    subtask.status = "done"
                    subtask.result = exec_result.output
                    self.context.add_turn("Coder", f"Completed: {subtask.description}\nResult: {exec_result.output[:200]}...")
                else:
                    subtask.status = "failed"
                    subtask.error = str(exec_result.errors)
                    all_done = False
                    # 如果编码失败，直接进入自愈或失败
                    state.status = DevStatus.FAILED 
                    return

        if all_done:
            state.status = DevStatus.TESTING

    async def _handle_testing(self, state: CouncilState):
        """处理测试阶段 - 独立运行测试"""
        state.log("🧪 运行测试...")
        
        # 运行测试（不进入自愈循环）
        test_result = self.healing_loop.run_tests()
        
        state.test_results.append({
            "passed": test_result.passed,
            "total": test_result.total_tests,
            "passed_count": test_result.passed_count,
            "failed_count": test_result.failed_count,
        })
        
        if test_result.passed:
            state.log(f"✅ 测试通过: {test_result.passed_count}/{test_result.total_tests}")
            state.status = DevStatus.REVIEWING  # 直接进入审查
        else:
            state.log(f"❌ 测试失败: {test_result.failed_count} 个失败")
            state.status = DevStatus.HEALING  # 需要自愈

    async def _handle_healing(self, state: CouncilState):
        """处理自愈阶段"""
        report = self.healing_loop.run()
        state.test_results.append({
            "status": report.status.value,
            "iterations": report.iterations,
            "error": report.final_error
        })
        state.log(f"🔧 自愈结果: {report.status.value}")
        
        # 记录自愈结果到上下文
        self.context.add_turn("System", f"Self-Healing Report: Status={report.status.value}, Iterations={report.iterations}, Error={report.final_error}")

        # 无论成功与否，都进入审查阶段 (由 Council 决定是否通过)
        state.status = DevStatus.REVIEWING

    async def _handle_reviewing(self, state: CouncilState):
        """处理审查阶段 (Council Meeting)"""
        votes = await self._hold_council_meeting(state)
        
        consensus = self.consensus.evaluate(votes)
        state.log(f"⚖️ 共识结果: {consensus.decision.value} (π={consensus.pi_approve:.2f})")
        
        if consensus.decision == ConsensusDecision.AUTO_COMMIT:
            state.status = DevStatus.COMPLETED
        elif consensus.decision == ConsensusDecision.REJECT:
            # 拒绝 -> 回退到规划 (或失败)
            # 简单起见，如果拒绝，我们标记为失败，或者可以增加 retry 计数
            state.status = DevStatus.FAILED
            state.log(f"❌ 提案被拒绝: {consensus.reason}")
        else:
            state.status = DevStatus.HUMAN_REQUIRED
            state.log(f"⚠️ 需要人工介入: {consensus.reason}")

    async def _hold_council_meeting(self, state: CouncilState) -> List[Dict[str, Any]]:
        """召开理事会会议"""
        votes = []
        
        # 提案摘要
        latest_test = state.test_results[-1] if state.test_results else {}
        proposal = f"""
任务: {state.task}
计划: {len(state.plan.subtasks) if state.plan else 0} 个子任务
测试状态: {latest_test.get('status', 'unknown')}
"""
        # 1. Reviewer
        r_vote = self.reviewer.vote_structured(proposal, context={"history": self.context.get_context_for_prompt()})
        votes.append(r_vote.to_legacy_dict())
        state.review_comments.append(f"Reviewer: {r_vote.blocking_reason or 'LGTM'}")
        self.context.add_turn("Reviewer", f"Vote: {r_vote.vote.value}. Reason: {r_vote.blocking_reason or 'LGTM'}")

        # 2. Architect
        a_vote = self.architect.vote_structured(proposal, context={"history": self.context.get_context_for_prompt()})
        votes.append(a_vote.to_legacy_dict())
        self.context.add_turn("Architect", f"Vote: {a_vote.vote.value}. Reason: {a_vote.blocking_reason or 'LGTM'}")

        # 3. Coder
        c_vote = self.coder.vote_structured(proposal, context={"history": self.context.get_context_for_prompt()})
        votes.append(c_vote.to_legacy_dict())
        self.context.add_turn("Coder", f"Vote: {c_vote.vote.value}. Reason: {c_vote.blocking_reason or 'LGTM'}")

        return votes


# 导出
__all__ = ["DevOrchestrator"]
