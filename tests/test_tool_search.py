"""
Tests for Tool Search - 动态工具发现与延迟加载
"""

import pytest
from council.mcp.tool_search import (
    ToolSearchTool,
    ToolRegistry,
    ToolDefinition,
    ToolCategory,
    create_default_registry,
    DEFAULT_TOOLS,
)


class TestToolDefinition:
    """ToolDefinition 测试"""

    def test_create_tool_definition(self):
        """测试创建工具定义"""
        tool = ToolDefinition(
            name="test_tool",
            description="A test tool",
            category=ToolCategory.CODE,
            keywords=["test", "example"],
        )

        assert tool.name == "test_tool"
        assert tool.defer_loading is True  # 默认延迟加载
        assert tool.token_cost == 100

    def test_matches_exact_name(self):
        """测试名称精确匹配"""
        tool = ToolDefinition(
            name="read_file",
            description="Read file content",
            category=ToolCategory.FILESYSTEM,
        )

        score = tool.matches("read_file")
        assert score == 1.0

    def test_matches_keyword(self):
        """测试关键词匹配"""
        tool = ToolDefinition(
            name="grep_search",
            description="Search in files",
            category=ToolCategory.SEARCH,
            keywords=["grep", "search", "搜索"],
        )

        score = tool.matches("我想搜索文件")
        assert score > 0.1

    def test_matches_low_score_for_unrelated(self):
        """测试不相关查询得分低"""
        tool = ToolDefinition(
            name="git_commit",
            description="Commit changes",
            category=ToolCategory.GIT,
            keywords=["git", "commit"],
        )

        score = tool.matches("读取数据库")
        assert score < 0.3


class TestToolRegistry:
    """ToolRegistry 测试"""

    def test_register_and_get(self):
        """测试注册和获取工具"""
        registry = ToolRegistry()
        tool = ToolDefinition(
            name="test_tool", description="Test", category=ToolCategory.CODE
        )

        registry.register(tool)

        assert registry.get("test_tool") == tool
        assert registry.get("nonexistent") is None

    def test_register_many(self):
        """测试批量注册"""
        registry = ToolRegistry()
        registry.register_many(DEFAULT_TOOLS)

        assert len(registry.tools) == len(DEFAULT_TOOLS)

    def test_load_and_unload(self):
        """测试加载和卸载"""
        registry = ToolRegistry()
        tool = ToolDefinition(
            name="test_tool",
            description="Test",
            category=ToolCategory.CODE,
            token_cost=100,
        )
        registry.register(tool)

        # 初始未加载
        assert not registry.is_loaded("test_tool")

        # 加载
        registry.load("test_tool")
        assert registry.is_loaded("test_tool")
        assert registry.get_loaded_token_cost() == 100

        # 卸载
        registry.unload("test_tool")
        assert not registry.is_loaded("test_tool")
        assert registry.get_loaded_token_cost() == 0


class TestToolSearchTool:
    """ToolSearchTool 测试"""

    @pytest.fixture
    def searcher(self):
        """创建测试用搜索器"""
        registry = create_default_registry()
        return ToolSearchTool(registry, max_loaded_tokens=1000)

    def test_search_by_name(self, searcher):
        """测试按名称搜索"""
        results = searcher.search("read_file")

        assert len(results) > 0
        assert results[0].name == "read_file"

    def test_search_by_description(self, searcher):
        """测试按描述搜索"""
        results = searcher.search("读取文件")

        assert len(results) > 0
        # 应该找到 read_file
        names = [r.name for r in results]
        assert "read_file" in names

    def test_search_top_k(self, searcher):
        """测试 top_k 限制"""
        results = searcher.search("file", top_k=2)

        assert len(results) <= 2

    def test_search_by_category(self, searcher):
        """测试分类过滤"""
        results = searcher.search("", category=ToolCategory.GIT)

        for tool in results:
            assert tool.category == ToolCategory.GIT

    def test_search_and_load(self, searcher):
        """测试搜索并加载"""
        loaded = searcher.search_and_load("file", top_k=2)

        assert len(loaded) > 0
        for tool in loaded:
            assert searcher.registry.is_loaded(tool.name)

    def test_respects_token_budget(self, searcher):
        """测试 Token 预算限制"""
        searcher.max_loaded_tokens = 150  # 很小的预算

        loaded = searcher.search_and_load("file git search", top_k=5)

        # 不应该超过预算
        total_cost = sum(t.token_cost for t in loaded)
        assert total_cost <= 150

    def test_get_context_schema(self, searcher):
        """测试获取上下文 Schema"""
        searcher.load("read_file")
        searcher.load("write_file")

        schema = searcher.get_context_schema()

        assert "read_file" in schema
        assert "write_file" in schema
        assert "description" in schema["read_file"]

    def test_get_stats(self, searcher):
        """测试获取统计信息"""
        searcher.load("read_file")

        stats = searcher.get_stats()

        assert stats["total_tools"] == len(DEFAULT_TOOLS)
        assert stats["loaded_tools"] == 1
        assert "budget_usage_percent" in stats


class TestDefaultTools:
    """默认工具测试"""

    def test_default_tools_exist(self):
        """测试默认工具存在"""
        assert len(DEFAULT_TOOLS) > 0

    def test_all_have_defer_loading(self):
        """测试所有工具都启用延迟加载"""
        for tool in DEFAULT_TOOLS:
            assert tool.defer_loading is True

    def test_create_default_registry(self):
        """测试创建默认注册中心"""
        registry = create_default_registry()

        assert len(registry.tools) == len(DEFAULT_TOOLS)
        assert registry.get("read_file") is not None
