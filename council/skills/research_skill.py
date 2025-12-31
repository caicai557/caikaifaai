from typing import Dict, Any, List, Optional, Callable, Awaitable
from pydantic import BaseModel, Field
import asyncio
import logging
from .base_skill import BaseSkill
from council.observability.tracer import AgentTracer

logger = logging.getLogger(__name__)


class ResearchInput(BaseModel):
    """研究任务输入"""

    topic: str = Field(..., description="研究主题")
    depth: int = Field(3, description="研究深度 (浏览页面数)", ge=1, le=10)


class ResearchOutput(BaseModel):
    """研究任务输出"""

    topic: str
    sources: List[str]
    summary: str
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ResearchSkill(BaseSkill):
    """
    研究技能 (ResearchSkill)

    流程:
    1. 搜索相关信息 (Search)
    2. 浏览关键页面 (Browse)
    3. 汇总生成报告 (Summarize)

    Features:
    - Pydantic 类型检查
    - OpenTelemetry 追踪
    - 依赖注入
    - 错误处理与重试
    """

    def __init__(
        self,
        llm_client=None,
        search_tool: Optional[Callable[[str], Awaitable[List[str]]]] = None,
        browse_tool: Optional[Callable[[str], Awaitable[str]]] = None,
        tracer: Optional[AgentTracer] = None,
        approval_callback: Optional[Callable] = None,
        progress_callback: Optional[Callable] = None,
    ):
        super().__init__(
            name="ResearchSkill",
            description="Deep research on a topic using search and browse tools",
            llm_client=llm_client,
            approval_callback=approval_callback,
            progress_callback=progress_callback,
        )
        self.tools = {
            "search": search_tool or self._mock_search,
            "browse": browse_tool or self._mock_browse,
        }
        self.tracer = tracer or AgentTracer("research-skill")

    async def execute(self, topic: str, depth: int = 3, **kwargs) -> Dict[str, Any]:
        """
        执行研究任务

        Args:
            topic: 研究主题
            depth: 研究深度
        """
        # 1. 验证输入
        try:
            input_data = ResearchInput(topic=topic, depth=depth)
        except Exception as e:
            logger.error(f"Input validation failed: {e}")
            raise ValueError(f"Invalid input: {e}")

        with self.tracer.trace_agent_step("ResearchSkill", "execute") as span:
            span.set_attribute("topic", input_data.topic)
            span.set_attribute("depth", input_data.depth)

            logger.info(f"🔍 [ResearchSkill] 开始研究: {input_data.topic}")

            try:
                # 2. 搜索
                with self.tracer.trace_tool_call("search", {"query": input_data.topic}):
                    search_results = await self.tools["search"](input_data.topic)

                logger.info(f"📑 [ResearchSkill] 找到 {len(search_results)} 个相关结果")

                if not search_results:
                    return ResearchOutput(
                        topic=input_data.topic,
                        sources=[],
                        summary="No sources found.",
                        metadata={"status": "no_results"},
                    ).model_dump()

                # 3. 浏览 (并发)
                tasks = []
                target_urls = search_results[: input_data.depth]

                for url in target_urls:
                    tasks.append(self._safe_browse(url))

                contents = await asyncio.gather(*tasks)
                valid_contents = [c for c in contents if c]

                logger.info(
                    f"📖 [ResearchSkill] 已浏览 {len(valid_contents)}/{len(target_urls)} 个页面"
                )

                # 4. 总结
                with self.tracer.trace_llm_call(
                    "summarizer", f"Summarize {len(valid_contents)} sources"
                ):
                    summary = await self._summarize(input_data.topic, valid_contents)

                # 5. 构造输出
                output = ResearchOutput(
                    topic=input_data.topic,
                    sources=target_urls,
                    summary=summary,
                    metadata={
                        "total_sources": len(search_results),
                        "browsed_count": len(valid_contents),
                    },
                )

                return output.model_dump()

            except Exception as e:
                logger.error(f"Research failed: {e}", exc_info=True)
                span.set_attribute("error", str(e))
                raise RuntimeError(f"Research execution failed: {e}")

    async def _safe_browse(self, url: str) -> Optional[str]:
        """安全浏览，带错误处理"""
        try:
            with self.tracer.trace_tool_call("browse", {"url": url}):
                return await self.tools["browse"](url)
        except Exception as e:
            logger.warning(f"Failed to browse {url}: {e}")
            return None

    async def _mock_search(self, query: str) -> List[str]:
        """模拟搜索工具"""
        await asyncio.sleep(0.5)
        return [f"https://example.com/result{i}?q={query}" for i in range(1, 6)]

    async def _mock_browse(self, url: str) -> str:
        """模拟浏览工具"""
        await asyncio.sleep(0.5)
        return f"Content from {url}: This is relevant information about the topic."

    async def _summarize(self, topic: str, contents: List[str]) -> str:
        """总结内容"""
        if not contents:
            return "No content available to summarize."

        if self.llm_client:
            # 实际 LLM 调用逻辑
            # 限制每个来源的长度，防止 Token 爆炸
            truncated_contents = []
            total_chars = 0
            MAX_CHARS_PER_SOURCE = 2000
            MAX_TOTAL_CHARS = 10000

            for c in contents:
                if total_chars >= MAX_TOTAL_CHARS:
                    break

                truncated = c[:MAX_CHARS_PER_SOURCE]
                if len(c) > MAX_CHARS_PER_SOURCE:
                    truncated += "...(truncated)"

                truncated_contents.append(truncated)
                total_chars += len(truncated)

            prompt = (
                f"Topic: {topic}\n\nSources:\n"
                + "\n".join(truncated_contents)
                + "\n\nSummarize:"
            )
            complete = getattr(self.llm_client, "complete", None)
            if not callable(complete):
                raise NotImplementedError("llm_client must provide complete()")
            result = complete(prompt)
            if asyncio.iscoroutine(result):
                result = await result
            return result

        return f"Auto-generated summary for {topic}: Found {len(contents)} relevant sources containing key insights."
