"""
Composite Tools - 聚合工具

将多个底层工具组合成高级工具:
- deep_research: 聚合搜索+浏览+摘要
- code_analyze: 聚合静态分析+安全扫描
"""

from typing import Dict, List, Any, Optional  # noqa: F401
import logging

logger = logging.getLogger(__name__)


class CompositeTools:
    """
    聚合工具集

    将多个工具调用组合成单个高级操作,
    减少 LLM 调用次数并提高效率

    Usage:
        tools = CompositeTools(
            web_tools=web_client,
            code_tools=code_analyzer,
            llm_client=llm
        )

        # 深度研究
        result = await tools.deep_research("AI agent 最佳实践 2025")

        # 代码分析
        result = await tools.code_analyze("/path/to/file.py")
    """

    def __init__(
        self,
        web_tools=None,
        code_tools=None,
        llm_client=None,
        memory_aggregator=None,
    ):
        """
        初始化聚合工具

        Args:
            web_tools: Web 搜索/浏览工具
            code_tools: 代码分析工具
            llm_client: LLM 客户端 (用于摘要)
            memory_aggregator: 记忆聚合器 (用于存储结果)
        """
        self.web_tools = web_tools
        self.code_tools = code_tools
        self.llm_client = llm_client
        self.memory_aggregator = memory_aggregator

    async def deep_research(
        self,
        topic: str,
        max_sources: int = 5,
        max_chars_per_source: int = 2000,
    ) -> Dict[str, Any]:
        """
        深度研究: 搜索 + 浏览 + 摘要

        Args:
            topic: 研究主题
            max_sources: 最大来源数
            max_chars_per_source: 每个来源最大字符数

        Returns:
            {
                "summary": "综合摘要",
                "sources": [{"url": "...", "title": "...", "content": "..."}],
                "key_findings": ["..."],
            }
        """
        result = {
            "summary": "",
            "sources": [],
            "key_findings": [],
            "topic": topic,
        }

        # Step 1: 搜索
        search_results = []
        if self.web_tools and hasattr(self.web_tools, "search"):
            try:
                search_results = await self.web_tools.search(topic, limit=max_sources)
            except Exception as e:
                logger.warning(f"Search failed: {e}")

        # Step 2: 浏览各个来源
        for item in search_results[:max_sources]:
            url = item.get("url", "")
            if not url:
                continue

            content = ""
            if self.web_tools and hasattr(self.web_tools, "browse"):
                try:
                    content = await self.web_tools.browse(url)
                    content = content[:max_chars_per_source]
                except Exception as e:
                    logger.warning(f"Browse failed for {url}: {e}")

            result["sources"].append(
                {
                    "url": url,
                    "title": item.get("title", ""),
                    "content": content,
                }
            )

        # Step 3: 使用 LLM 生成摘要
        if self.llm_client and result["sources"]:
            try:
                sources_text = "\n\n".join(
                    f"[{s['title']}]\n{s['content'][:1000]}" for s in result["sources"]
                )

                prompt = f"""基于以下研究资料，请总结关于 "{topic}" 的关键发现:

{sources_text}

请输出:
1. 简洁摘要 (200字以内)
2. 3-5 个关键发现
"""
                import asyncio

                complete = getattr(self.llm_client, "complete", None)
                if callable(complete):
                    response = complete(prompt)
                    if asyncio.iscoroutine(response):
                        response = await response
                    result["summary"] = response
            except Exception as e:
                logger.warning(f"Summary generation failed: {e}")

        # Step 4: 存储到记忆 (如果可用)
        if self.memory_aggregator and result["summary"]:
            try:
                self.memory_aggregator.remember(
                    f"[Research] {topic}: {result['summary'][:500]}",
                    memory_type="long_term",
                    metadata={"type": "research", "topic": topic},
                )
            except Exception:
                pass

        return result

    async def code_analyze(
        self,
        file_path: str,
        include_security: bool = True,
        include_quality: bool = True,
    ) -> Dict[str, Any]:
        """
        代码分析: 静态分析 + 安全扫描 + 复杂度

        Args:
            file_path: 文件路径
            include_security: 是否包含安全扫描
            include_quality: 是否包含质量检查

        Returns:
            {
                "file": "...",
                "security_issues": [...],
                "quality_issues": [...],
                "complexity": {...},
                "summary": "...",
            }
        """
        result = {
            "file": file_path,
            "security_issues": [],
            "quality_issues": [],
            "complexity": {},
            "summary": "",
        }

        if not self.code_tools:
            result["summary"] = "No code analysis tools available"
            return result

        # Step 1: 安全扫描
        if include_security and hasattr(self.code_tools, "security_scan"):
            try:
                security = await self.code_tools.security_scan(file_path)
                result["security_issues"] = security.get("issues", [])
            except Exception as e:
                logger.warning(f"Security scan failed: {e}")

        # Step 2: 质量检查
        if include_quality and hasattr(self.code_tools, "quality_check"):
            try:
                quality = await self.code_tools.quality_check(file_path)
                result["quality_issues"] = quality.get("issues", [])
            except Exception as e:
                logger.warning(f"Quality check failed: {e}")

        # Step 3: 复杂度分析
        if hasattr(self.code_tools, "complexity_analysis"):
            try:
                result["complexity"] = await self.code_tools.complexity_analysis(
                    file_path
                )
            except Exception as e:
                logger.warning(f"Complexity analysis failed: {e}")

        # Step 4: 生成摘要
        issues_count = len(result["security_issues"]) + len(result["quality_issues"])
        result["summary"] = (
            f"分析完成: 发现 {len(result['security_issues'])} 个安全问题, "
            f"{len(result['quality_issues'])} 个质量问题"
        )

        return result

    def get_tool_definitions(self) -> List[Dict[str, Any]]:
        """
        获取工具定义 (用于 MCP 注册)

        Returns:
            工具定义列表
        """
        return [
            {
                "name": "deep_research",
                "description": "深度研究工具 - 自动搜索、浏览和摘要多个来源",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "topic": {"type": "string", "description": "研究主题"},
                        "max_sources": {
                            "type": "integer",
                            "default": 5,
                            "description": "最大来源数",
                        },
                    },
                    "required": ["topic"],
                },
            },
            {
                "name": "code_analyze",
                "description": "代码分析工具 - 聚合安全扫描和质量检查",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "file_path": {
                            "type": "string",
                            "description": "要分析的文件路径",
                        },
                        "include_security": {
                            "type": "boolean",
                            "default": True,
                            "description": "是否包含安全扫描",
                        },
                        "include_quality": {
                            "type": "boolean",
                            "default": True,
                            "description": "是否包含质量检查",
                        },
                    },
                    "required": ["file_path"],
                },
            },
        ]


__all__ = ["CompositeTools"]
