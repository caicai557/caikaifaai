"""
WebSurfer - 网络冲浪者智能体
负责联网搜索资料、查阅文档和事实核查
"""

from typing import Optional, Dict, Any
from council.agents.base_agent import (
    BaseAgent,
    Vote,
    VoteDecision,
    ThinkResult,
    ExecuteResult,
)

WEB_SURFER_SYSTEM_PROMPT = """你是一名专业的网络信息检索员 (WebSurfer)。

## 核心职责
1. **文档检索**: 查找最新的库文档、API 参考
2. **事实核查**:不仅限于假设，通过搜索确认技术细节
3. **竞品分析**: 调研类似项目的架构和实现
4. **错误调试**: 搜索报错信息和解决方案

## 工具能力 (Mock)
- 你可以使用 `search_web(query)` 来获取信息 (目前由系统环境提供)
- 你应当假设你可以访问互联网

## 输出原则
- **准确第一**: 不要编造 URL 或版本号
- **引用来源**: 尽可能提供信息来源 URL
- **摘要总结**: 不要复制粘贴整个页面，提供关键信息摘要

## 行为模式
- 如果任务需要外部知识，主动提出需要搜索
- 对于不确定的技术选型，建议先进行调研
"""


class WebSurfer(BaseAgent):
    """
    网络冲浪者智能体
    """

    def __init__(
        self, model: str = "gemini-2.0-flash", llm_client: Optional[Any] = None
    ):
        super().__init__(
            name="WebSurfer",
            system_prompt=WEB_SURFER_SYSTEM_PROMPT,
            model=model,
            llm_client=llm_client,
        )

    def think(self, task: str, context: Optional[Dict[str, Any]] = None) -> ThinkResult:
        """
        分析搜索任务
        """
        prompt = f"""
任务: {task}
上下文: {context or {}}

作为 WebSurfer，分析此任务是否需要联网搜索。如果需要，列出搜索关键词。
返回格式:
Summary: [摘要]
Queries: [关键词1, 关键词2]
Confidence: [0.0-1.0]
"""
        response = self._call_llm(prompt)

        # 简单解析 (实际应使用 structured_output)
        return ThinkResult(
            analysis=response,
            concerns=[],
            suggestions=["使用 Google Search", "查阅官方文档"],
            confidence=0.9,
            context={"role": "web_surfer"},
        )

    def vote(self, proposal: str, context: Optional[Dict[str, Any]] = None) -> Vote:
        """
        WebSurfer 通常不参与核心架构投票，除非涉及引用了错误的外部事实
        """
        return Vote(
            agent_name=self.name,
            decision=VoteDecision.APPROVE,
            confidence=0.8,
            rationale="除非包含明显的事实错误，否则我保持中立。",
        )

    def execute(
        self, task: str, plan: Optional[Dict[str, Any]] = None
    ) -> ExecuteResult:
        """
        执行搜索任务
        """
        # 在真实环境中，这里会调用 search_web 工具
        # 目前模拟返回

        return ExecuteResult(
            success=True,
            output=f"已根据 '{task}' 完成搜索 (模拟)。发现 LiteLLM 最新文档支持 Pydantic 结构化输出。",
            changes_made=["检索了相关文档"],
        )

    # Structured Protocol Methods
    def think_structured(self, task: str, context: Optional[Dict[str, Any]] = None):
        from council.protocol.schema import MinimalThinkResult

        prompt = f"""
        任务: {task}
        请制定搜索策略。
        """
        result = self._call_llm_structured(prompt, MinimalThinkResult)
        result.perspective = "research"

        self.add_to_history(
            {
                "action": "think_structured",
                "task": task[:100],
                "confidence": result.confidence,
            }
        )
        return result

    def vote_structured(self, proposal: str, context: Optional[Dict[str, Any]] = None):
        from council.protocol.schema import MinimalVote

        prompt = f"""
        提案: {proposal}
        请检查是否有事实性错误。
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
