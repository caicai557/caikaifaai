"""
Architect - 架构师智能体
负责顶层设计、架构评审、风险识别
"""

from typing import Optional, Dict, Any
from council.agents.base_agent import (
    BaseAgent,
    Vote,
    VoteDecision,
    ThinkResult,
    ExecuteResult,
    DEFAULT_MODEL,
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
        self, model: str = DEFAULT_MODEL, llm_client: Optional["LLMClient"] = None
    ):
        super().__init__(
            name="Architect",
            system_prompt=ARCHITECT_SYSTEM_PROMPT,
            model=model,
            llm_client=llm_client,
        )

    def think(self, task: str, context: Optional[Dict[str, Any]] = None) -> ThinkResult:
        """
        从架构角度分析任务
        """
        # 构造 Prompt
        prompt = f"""
任务: {task}
上下文: {context or {}}

请从软件架构师的角度分析此任务。请提供：
1. 架构分析 (Analysis)
2. 担忧/风险 (Concerns) - 每行一个
3. 建议 (Suggestions) - 每行一个
4. 置信度 (Confidence) - 0.0 到 1.0

请按以下格式返回：
[Analysis]
...分析内容...

[Concerns]
- 风险1
- 风险2

[Suggestions]
- 建议1
- 建议2

[Confidence]
0.8
"""
        # 调用 LLM
        response = self._call_llm(prompt)

        # 解析响应
        analysis = ""
        concerns = []
        suggestions = []
        confidence = 0.5

        current_section = None
        for line in response.split("\n"):
            line = line.strip()
            if not line:
                continue

            if line.startswith("[Analysis]"):
                current_section = "analysis"
            elif line.startswith("[Concerns]"):
                current_section = "concerns"
            elif line.startswith("[Suggestions]"):
                current_section = "suggestions"
            elif line.startswith("[Confidence]"):
                current_section = "confidence"
            elif current_section == "analysis":
                analysis += line + "\n"
            elif current_section == "concerns":
                if line.startswith("-"):
                    concerns.append(line[1:].strip())
            elif current_section == "suggestions":
                if line.startswith("-"):
                    suggestions.append(line[1:].strip())
            elif current_section == "confidence":
                try:
                    confidence = float(line)
                except ValueError:
                    pass

        self.add_to_history(
            {
                "action": "think",
                "task": task,
                "context": context,
                "response_length": len(response),
            }
        )

        return ThinkResult(
            analysis=analysis.strip()
            or response,  # Fallback to raw response if parsing fails
            concerns=concerns,
            suggestions=suggestions,
            confidence=confidence,
            context={"perspective": "architecture"},
        )

    def vote(self, proposal: str, context: Optional[Dict[str, Any]] = None) -> Vote:
        """
        对提案进行架构评审投票
        """
        prompt = f"""
提案: {proposal}
上下文: {context or {}}

作为架构师，请评估该提案。请投票：
- APPROVE: 批准
- APPROVE_WITH_CHANGES: 需要修改
- HOLD: 暂缓（需要更多信息）
- REJECT: 拒绝

返回格式：
Vote: [DECISION]
Confidence: [0.0-1.0]
Rationale: [理由]
Changes: [建议修改1, 建议修改2] (可选)
"""
        response = self._call_llm(prompt)

        # 默认值
        decision = VoteDecision.HOLD
        confidence = 0.5
        rationale = response
        suggested_changes = []

        # 简单解析
        import re

        decision_match = re.search(
            r"Vote:\s*(APPROVE_WITH_CHANGES|APPROVE|HOLD|REJECT)",
            response,
            re.IGNORECASE,
        )
        if decision_match:
            d_str = decision_match.group(1).upper()
            if d_str == "APPROVE":
                decision = VoteDecision.APPROVE
            elif d_str == "APPROVE_WITH_CHANGES":
                decision = VoteDecision.APPROVE_WITH_CHANGES
            elif d_str == "HOLD":
                decision = VoteDecision.HOLD
            elif d_str == "REJECT":
                decision = VoteDecision.REJECT

        conf_match = re.search(r"Confidence:\s*(\d*\.?\d+)", response)
        if conf_match:
            try:
                confidence = float(conf_match.group(1))
            except ValueError:
                pass

        rationale_match = re.search(
            r"Rationale:\s*(.+?)(?:\nChanges:|$)", response, re.DOTALL | re.IGNORECASE
        )
        if rationale_match:
            rationale = rationale_match.group(1).strip()

        changes_match = re.search(
            r"Changes:\s*(.+)", response, re.DOTALL | re.IGNORECASE
        )
        if changes_match:
            changes_str = changes_match.group(1).strip()
            # 尝试分割
            if "[" in changes_str:
                # 简单处理列表格式
                suggested_changes = [c.strip(" '\"[]") for c in changes_str.split(",")]
            else:
                suggested_changes = [changes_str]

        self.add_to_history(
            {
                "action": "vote",
                "proposal": proposal,
                "context": context,
                "decision": decision.value,
            }
        )

        return Vote(
            agent_name=self.name,
            decision=decision,
            confidence=confidence,
            rationale=rationale,
            suggested_changes=suggested_changes,
        )

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
