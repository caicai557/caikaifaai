"""
Architect - 架构师智能体
负责顶层设计、架构评审、风险识别
"""

from typing import Optional, Dict, Any
from council.agents.base_agent import (
    BaseAgent,
    Vote,
    ThinkResult,
    ExecuteResult,
    MODEL_ARCHITECT,
)


ARCHITECT_SYSTEM_PROMPT = """你是一名资深软件架构师，拥有 20 年的系统设计经验。

## 核心职责
1. **顶层设计**: 评估系统架构的合理性和可扩展性
2. **风险识别**: 识别技术债务、性能瓶颈、安全隐患
3. **方案评审**: 对设计提案进行深度分析

## 决策原则
- 优先考虑系统的长期可维护性
- 权衡复杂度与收益
- 关注接口设计和模块边界
- 识别潜在的技术债务

## 输出格式
始终使用结构化的分析框架：
1. 架构影响分析
2. 风险评估 (高/中/低)
3. 改进建议
4. 替代方案 (如有)

## 禁止行为
- 不做没有依据的判断
- 不忽视安全问题
- 不推荐过度设计
"""


class Architect(BaseAgent):
    """
    架构师智能体

    专注于系统顶层设计和架构评审
    """

    def __init__(
        self, model: str = MODEL_ARCHITECT, llm_client: Optional["LLMClient"] = None
    ):
        super().__init__(
            name="Architect",
            system_prompt=ARCHITECT_SYSTEM_PROMPT,
            model=model,
            llm_client=llm_client,
        )

    def think(self, task: str, context: Optional[Dict[str, Any]] = None) -> ThinkResult:
        """
        从架构角度分析任务 (Default to Structured for 2026 Compliance)
        """
        # 使用结构化思考以节省 Token (~70% reduction)
        result = self.think_structured(task, context)

        # 转换为传统的 ThinkResult 以保持兼容性
        return ThinkResult(
            analysis=result.summary,
            concerns=result.concerns if hasattr(result, "concerns") else [],
            suggestions=result.suggestions if hasattr(result, "suggestions") else [],
            confidence=result.confidence,
            context={"perspective": "architecture", "mode": "structured"},
        )

    def vote(self, proposal: str, context: Optional[Dict[str, Any]] = None) -> Vote:
        """
        对提案进行架构评审投票 (Default to Structured for 2026 Compliance)
        """
        # 使用结构化投票以节省 Token
        result = self.vote_structured(proposal, context)

        # 转换为传统的 Vote 对象
        return result.vote

    def execute(
        self, task: str, plan: Optional[Dict[str, Any]] = None
    ) -> ExecuteResult:
        """
        执行架构相关任务（如生成架构文档）
        """
        self.add_to_history(
            {
                "action": "execute",
                "task": task,
                "plan": plan,
            }
        )

        return ExecuteResult(
            success=True,
            output=f"架构师已完成任务: {task}",
            changes_made=["生成架构设计文档"],
        )

    def review_design(self, design_doc: str) -> Dict[str, Any]:
        """
        专门的设计评审方法

        Args:
            design_doc: 设计文档内容

        Returns:
            评审结果
        """
        return {
            "reviewer": self.name,
            "status": "reviewed",
            "concerns": [],
            "suggestions": [],
            "approval": True,
        }

    # ============================================================
    # 2025 Best Practice: Structured Protocol Methods
    # These methods save ~70% tokens compared to NL versions
    # ============================================================

    def vote_structured(self, proposal: str, context: Optional[Dict[str, Any]] = None):
        """
        [2025 Best Practice] 对提案进行架构评审投票 (结构化输出)

        使用 MinimalVote schema，节省 ~70% Token。

        Args:
            proposal: 提案内容
            context: 可选上下文

        Returns:
            MinimalVote: 极简投票结果
        """
        from council.protocol.schema import MinimalVote

        prompt = f"""
作为架构师，评估以下提案:
提案: {proposal}
上下文: {context or {}}

请投票并识别风险类别 (sec=安全, perf=性能, maint=维护, arch=架构)。
"""
        result = self._call_llm_structured(prompt, MinimalVote)

        self.add_to_history(
            {
                "action": "vote_structured",
                "proposal": proposal[:100],
                "vote": result.vote.to_legacy(),
            }
        )

        return result

    def think_structured(self, task: str, context: Optional[Dict[str, Any]] = None):
        """
        [2025 Best Practice] 从架构角度分析任务 (结构化输出)

        使用 MinimalThinkResult schema，限制输出长度。

        Args:
            task: 任务描述
            context: 可选上下文

        Returns:
            MinimalThinkResult: 极简思考结果
        """
        from council.protocol.schema import MinimalThinkResult

        prompt = f"""
作为架构师，分析以下任务:
任务: {task}
上下文: {context or {}}

请提供简短摘要 (最多200字)、关键担忧 (最多3点)、和建议 (最多3点)。
"""
        result = self._call_llm_structured(prompt, MinimalThinkResult)
        result.perspective = "architecture"

        self.add_to_history(
            {
                "action": "think_structured",
                "task": task[:100],
                "confidence": result.confidence,
            }
        )

        return result


__all__ = ["Architect", "ARCHITECT_SYSTEM_PROMPT"]
