"""
Orchestrator - 理事会主席智能体 (Council Chairman)

层级化监督模式的核心：
- 对接用户需求
- 拆解为子任务
- 分发给专业执行代理
- 汇总结果并决策
"""

from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from council.agents.base_agent import (
    BaseAgent,
    Vote,
    VoteDecision,
    ThinkResult,
    ExecuteResult,
    DEFAULT_MODEL,
)
from council.orchestration.ledger import DualLedger
from council.governance.gateway import DecisionType, GovernanceGateway


ORCHESTRATOR_SYSTEM_PROMPT = """你是理事会主席 (Council Chairman)，负责统筹协调所有专家智能体。

## 核心职责
1. **需求拆解**: 将用户需求分解为可执行的子任务
2. **任务分发**: 根据专长将任务分配给合适的执行代理
3. **进度监控**: 追踪每个代理的执行状态
4. **决策汇总**: 综合各方意见形成最终决定

## 可用执行代理
- **Architect**: 架构设计、系统分析
- **Coder**: 代码实现、测试编写
- **SecurityAuditor**: 安全审计、合规检查
- **WebSurfer**: 网络检索、文档查阅 (如有)

## 工作原则
- 最小化干预: 信任专家，不过度指导
- 清晰边界: 明确每个任务的范围和验收标准
- 及时止损: 发现阻塞时果断重规划
- 人类优先: 关键决策等待人工确认

## 输出格式 (任务拆解)
```
[TASK_DECOMPOSITION]
1. {子任务描述} -> {执行代理} | 优先级: {P0/P1/P2}
2. ...
[/TASK_DECOMPOSITION]
```
"""


@dataclass
class SubTask:
    """子任务"""

    id: str
    description: str
    assigned_agent: str
    priority: str  # P0, P1, P2
    status: str = "pending"  # pending, in_progress, completed, blocked
    result: Optional[Dict[str, Any]] = None


@dataclass
class DecompositionResult:
    """任务拆解结果"""

    original_goal: str
    subtasks: List[SubTask]
    execution_order: List[str]  # SubTask IDs in order
    estimated_complexity: str  # low, medium, high


class Orchestrator(BaseAgent):
    """
    理事会主席智能体

    层级化监督模式的核心实现：
    1. 接收用户需求
    2. 拆解为子任务
    3. 分发给专业代理
    4. 汇总结果
    """

    # 可用的执行代理及其专长
    AVAILABLE_AGENTS = {
        "Architect": ["architecture", "design", "system", "structure", "api"],
        "Coder": ["implement", "code", "test", "function", "class", "bug", "fix"],
        "SecurityAuditor": [
            "security",
            "audit",
            "vulnerability",
            "compliance",
            "permission",
        ],
    }

    DECISION_KEYWORDS = {
        DecisionType.ARCHITECTURE_CHANGE: [
            "architecture",
            "re-architect",
            "redesign",
            "migration",
            "migrate",
            "架构",
            "重构",
            "重写",
        ],
        DecisionType.DEPLOY_STRATEGY: [
            "deploy",
            "release",
            "rollout",
            "canary",
            "blue-green",
            "上线",
            "发布",
        ],
        DecisionType.SECURITY_EXCEPTION: [
            "exception",
            "bypass",
            "skip security",
            "disable auth",
            "临时放开",
            "忽略安全",
        ],
        DecisionType.DATA_RETENTION: [
            "retention",
            "archive",
            "purge",
            "data retention",
            "保留策略",
            "删除数据",
        ],
        DecisionType.MODEL_SELECTION: [
            "model selection",
            "routing",
            "router",
            "model",
            "模型选择",
            "模型",
        ],
    }

    def __init__(
        self,
        model: str = DEFAULT_MODEL,
        governance_gateway: Optional[GovernanceGateway] = None,
        llm_client: Optional["LLMClient"] = None,
    ):
        super().__init__(
            name="Orchestrator",
            system_prompt=ORCHESTRATOR_SYSTEM_PROMPT,
            model=model,
            governance_gateway=governance_gateway,
            llm_client=llm_client,
        )
        self.active_subtasks: List[SubTask] = []
        self.ledger: Optional[DualLedger] = None

    def decompose(
        self, goal: str, context: Optional[Dict[str, Any]] = None
    ) -> DecompositionResult:
        """
        将用户目标拆解为子任务

        Args:
            goal: 用户目标
            context: 上下文信息

        Returns:
            DecompositionResult: 拆解结果
        """
        # 分析复杂度
        complexity = self._assess_complexity(goal)

        # 识别需要的代理
        required_agents = self._identify_agents(goal)

        # 生成子任务
        subtasks = []
        for i, agent in enumerate(required_agents):
            subtask = SubTask(
                id=f"ST-{i + 1:03d}",
                description=f"{agent} 负责: {self._extract_agent_task(goal, agent)}",
                assigned_agent=agent,
                priority="P0" if i == 0 else "P1",
            )
            subtasks.append(subtask)

        # 如果没有识别到代理，默认分配给 Coder
        if not subtasks:
            subtasks.append(
                SubTask(
                    id="ST-001",
                    description=f"Coder 实现: {goal}",
                    assigned_agent="Coder",
                    priority="P0",
                )
            )

        self.active_subtasks = subtasks

        # Initialize DualLedger for this task
        self.ledger = DualLedger.create(
            task_id=f"TASK-{id(goal) % 10000:04d}", goal=goal, max_stagnation=3
        )
        self.ledger.task.set_plan([st.description for st in subtasks])

        return DecompositionResult(
            original_goal=goal,
            subtasks=subtasks,
            execution_order=[st.id for st in subtasks],
            estimated_complexity=complexity,
        )

    def _assess_complexity(self, goal: str) -> str:
        """评估任务复杂度"""
        goal_lower = goal.lower()

        high_indicators = ["重构", "重写", "migrate", "全面", "系统", "架构"]
        low_indicators = ["修复", "fix", "typo", "格式", "简单", "小"]

        for ind in high_indicators:
            if ind in goal_lower:
                return "high"

        for ind in low_indicators:
            if ind in goal_lower:
                return "low"

        return "medium"

    def _identify_agents(self, goal: str) -> List[str]:
        """识别需要的执行代理"""
        goal_lower = goal.lower()
        required = []

        for agent, keywords in self.AVAILABLE_AGENTS.items():
            for kw in keywords:
                if kw in goal_lower:
                    if agent not in required:
                        required.append(agent)
                    break

        return required

    def _extract_agent_task(self, goal: str, agent: str) -> str:
        """为特定代理提取任务描述"""
        if agent == "Architect":
            return f"设计架构方案: {goal}"
        elif agent == "Coder":
            return f"实现并测试: {goal}"
        elif agent == "SecurityAuditor":
            return f"安全审计: {goal}"
        return goal

    def _infer_decision_types(self, goal: str) -> List[DecisionType]:
        """从任务描述中识别关键决策类型"""
        goal_lower = goal.lower()
        decisions: List[DecisionType] = []
        for decision_type, keywords in self.DECISION_KEYWORDS.items():
            if any(keyword in goal_lower for keyword in keywords):
                decisions.append(decision_type)
        return decisions

    def _request_decision_approvals(self, goal: str) -> Optional[ExecuteResult]:
        """对关键决策进行审批请求"""
        decisions = self._infer_decision_types(goal)
        for decision_type in decisions:
            description = f"关键决策: {decision_type.value}"
            approved = self.request_decision_approval(
                decision_type=decision_type,
                description=description,
                affected_resources=["orchestrator"],
                rationale="触发关键决策关键词，需要人工确认",
            )
            if not approved:
                return ExecuteResult(
                    success=False,
                    output=f"决策需要人工审批: {decision_type.value}",
                    errors=[f"Approval required for decision: {decision_type.value}"],
                )
        return None

    def dispatch(self, subtask: SubTask, agent: BaseAgent) -> ExecuteResult:
        """
        分发子任务给执行代理

        Args:
            subtask: 子任务
            agent: 执行代理

        Returns:
            ExecuteResult: 执行结果
        """
        subtask.status = "in_progress"

        # 调用代理执行
        try:
            result = agent.execute(subtask.description)
        except Exception as exc:
            error = f"{type(exc).__name__}: {exc}"
            result = ExecuteResult(
                success=False,
                output=f"执行代理失败: {error}",
                errors=[error],
            )

        if result.success:
            subtask.status = "completed"
        else:
            subtask.status = "blocked"

        subtask.result = {
            "success": result.success,
            "output": result.output,
            "changes": result.changes_made,
        }

        self.add_to_history(
            {
                "action": "dispatch",
                "subtask_id": subtask.id,
                "agent": agent.name,
                "result": subtask.status,
            }
        )

        # Record iteration in Progress Ledger
        if self.ledger:
            self.ledger.progress.record_iteration(
                progress=result.success,
                action=f"dispatch:{agent.name}",
                result=result.output[:100] if result.output else "",
            )

        return result

    def summarize(self) -> Dict[str, Any]:
        """
        汇总所有子任务结果

        Returns:
            汇总报告
        """
        completed = [st for st in self.active_subtasks if st.status == "completed"]
        blocked = [st for st in self.active_subtasks if st.status == "blocked"]
        pending = [st for st in self.active_subtasks if st.status == "pending"]

        return {
            "total": len(self.active_subtasks),
            "completed": len(completed),
            "blocked": len(blocked),
            "pending": len(pending),
            "success_rate": len(completed) / len(self.active_subtasks)
            if self.active_subtasks
            else 0,
            "subtasks": [
                {"id": st.id, "status": st.status, "agent": st.assigned_agent}
                for st in self.active_subtasks
            ],
        }

    def think(self, task: str, context: Optional[Dict[str, Any]] = None) -> ThinkResult:
        """分析任务并制定执行策略"""
        decomposition = self.decompose(task, context)

        analysis = f"""
任务拆解完成:
- 原始目标: {decomposition.original_goal}
- 复杂度: {decomposition.estimated_complexity}
- 子任务数: {len(decomposition.subtasks)}

执行顺序:
"""
        for st in decomposition.subtasks:
            analysis += (
                f"\n{st.id}. [{st.priority}] {st.assigned_agent}: {st.description}"
            )

        return ThinkResult(
            analysis=analysis,
            concerns=["需要监控各代理执行状态", "可能需要人工介入"],
            suggestions=["按优先级顺序执行", "定期检查进度账本"],
            confidence=0.8,
            context={"decomposition": decomposition},
        )

    def vote(self, proposal: str, context: Optional[Dict[str, Any]] = None) -> Vote:
        """作为主席对提案进行最终裁决"""
        # 主席通常会综合各方意见
        return Vote(
            agent_name=self.name,
            decision=VoteDecision.APPROVE,
            confidence=0.9,
            rationale="作为理事会主席，综合各方意见后批准此提案。",
        )

    def execute(
        self, task: str, plan: Optional[Dict[str, Any]] = None
    ) -> ExecuteResult:
        """执行编排任务"""
        decision_result = self._request_decision_approvals(task)
        if decision_result:
            return decision_result

        decomposition = self.decompose(task)

        self.add_to_history(
            {
                "action": "execute",
                "task": task,
                "subtasks": len(decomposition.subtasks),
            }
        )

        return ExecuteResult(
            success=True,
            output=f"理事会主席已完成任务拆解，生成 {len(decomposition.subtasks)} 个子任务",
            changes_made=[f"创建子任务: {st.id}" for st in decomposition.subtasks],
        )


__all__ = [
    "Orchestrator",
    "SubTask",
    "DecompositionResult",
    "ORCHESTRATOR_SYSTEM_PROMPT",
]
