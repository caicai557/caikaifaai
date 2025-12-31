"""
Reviewer - 审查者智能体
负责代码审查、质量把控、安全检查
"""

from typing import Optional, Dict, Any
from council.agents.base_agent import (
    BaseAgent,
    Vote,
    VoteDecision,
    ThinkResult,
    ExecuteResult,
)


REVIEWER_SYSTEM_PROMPT = """Role: Senior Code Reviewer & Security Auditor (Council Member)
Backstory: You are a strict Code Reviewer and Security Auditor. You have seen too many production outages caused by sloppy code. You are the gatekeeper of quality. You do not compromise on security.

Standard Operating Procedure (SOP):
1.  **Review Code**: Check for logic errors, security flaws (OWASP Top 10), and style violations (PEP 8).
2.  **Review Tests**: Ensure tests are comprehensive, cover edge cases, and actually test the logic.
3.  **Vote**: Approve only if the code meets the "Council Standards".
4.  **Output**: Provide specific, actionable feedback.

Constraints:
-   **Chain of Thought**: You MUST output your reasoning in <thinking>...</thinking> tags before generating JSON.
-   Security vulnerabilities are automatic blockers.
-   Missing tests are automatic blockers.
-   Be constructive but firm.
"""


class Reviewer(BaseAgent):
    """
    审查者智能体
    """

    def __init__(self, model: str = "gemini-2.0-flash"):
        super().__init__(
            name="Reviewer",
            system_prompt=REVIEWER_SYSTEM_PROMPT,
            model=model,
        )

    def think(self, task: str, context: Optional[Dict[str, Any]] = None) -> ThinkResult:
        """从审查角度分析任务"""
        # 复用结构化思考模式
        return self.think_structured(task, context)

    def vote(self, proposal: str, context: Optional[Dict[str, Any]] = None) -> Vote:
        """对提案进行审查投票"""
        # 复用结构化投票模式
        result = self.vote_structured(proposal, context)
        
        # 构造完整的 Vote 对象以兼容旧接口
        return Vote(
            agent_name=self.name,
            decision=VoteDecision(result.vote.to_legacy()),
            confidence=result.confidence,
            rationale=result.blocking_reason or "LGTM",
        )

    def execute(
        self, task: str, plan: Optional[Dict[str, Any]] = None
    ) -> ExecuteResult:
        """执行审查任务"""
        self.add_to_history({"action": "execute", "task": task})
        return ExecuteResult(
            success=True,
            output=f"审查完成: {task}",
            changes_made=[],
        )

    def vote_structured(self, proposal: str, context: Optional[Dict[str, Any]] = None):
        """[2025 Best Practice] 结构化投票"""
        from council.protocol.schema import MinimalVote
        
        prompt = f"""
作为审查者，评估以下提案:
提案: {proposal}
上下文: {context or {}}

请投票并识别风险。特别关注安全和质量问题。
"""
        result = self._call_llm_structured(prompt, MinimalVote)
        
        self.add_to_history({
            "action": "vote_structured",
            "proposal": proposal[:100],
            "vote": result.vote.to_legacy(),
        })
        
        return result

    def think_structured(self, task: str, context: Optional[Dict[str, Any]] = None):
        """[2025 Best Practice] 结构化思考"""
        from council.protocol.schema import MinimalThinkResult
        
        prompt = f"""
作为审查者，分析以下任务:
任务: {task}
上下文: {context or {}}

请提供简短摘要、关键担忧（安全/质量）、和建议。
"""
        result = self._call_llm_structured(prompt, MinimalThinkResult)
        result.perspective = "review"
        
        self.add_to_history({
            "action": "think_structured",
            "task": task[:100],
            "confidence": result.confidence,
        })
        
        return result

__all__ = ["Reviewer", "REVIEWER_SYSTEM_PROMPT"]
