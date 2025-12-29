from typing import Optional, Dict, Any
from council.agents.base_agent import BaseAgent, ExecuteResult, ThinkResult, Vote
from council.memory.vector_memory import VectorMemory
from council.streaming import StreamingLLM
import asyncio


class ResearchAgent(BaseAgent):
    """
    研究型 Agent，可以搜索记忆并生成报告。
    """

    def __init__(self):
        super().__init__(
            name="ResearchAgent",
            system_prompt="你是一个严谨的研究员。利用你的记忆查找事实。",
            model="claude-3-opus",
        )
        self.memory = VectorMemory(collection_name="research_data")
        self.llm = StreamingLLM()

        # 预置一些数据用于演示
        self.memory.add("Council 框架于 2025 年 12 月发布。", doc_id="fact1")
        self.memory.add("Council 使用共识机制进行决策。", doc_id="fact2")

    def think(self, task: str, context: Optional[Dict[str, Any]] = None) -> ThinkResult:
        return ThinkResult("我需要查询记忆库。", confidence=0.9)

    def vote(self, proposal: str, context: Optional[Dict[str, Any]] = None) -> Vote:
        return Vote(self.name, "approve", 1.0, "我相信我自己。")

    def execute(
        self, task: str, plan: Optional[Dict[str, Any]] = None
    ) -> ExecuteResult:
        # 1. 搜索记忆
        results = self.memory.search(task, k=2)
        context_text = "\n".join([r["document"] for r in results])

        # 2. 生成报告
        prompt = f"背景信息:\n{context_text}\n\n任务: {task}\n\n请生成一份简短报告。"

        # 为了演示简单起见使用同步包装，或者在 async 环境中运行
        # 由于 BaseAgent.execute 是同步的，我们在循环中运行 async stream
        report = asyncio.run(self.llm.stream_to_string(prompt, self.model))

        return ExecuteResult(True, report)


agent = ResearchAgent()
