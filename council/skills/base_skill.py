from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Callable, Awaitable

# 类型定义
ApprovalCallback = Callable[[str, Dict[str, Any]], Awaitable[bool]]
ProgressCallback = Callable[[str, int, int], Awaitable[None]]


class BaseSkill(ABC):
    """
    技能基类

    Skill 是对一组 Tool 和特定流程的封装，用于完成更复杂的任务。

    Features:
    - HITL (Human-in-the-Loop): 支持人工审批
    - Streaming: 支持进度汇报
    """

    def __init__(
        self,
        name: str,
        description: str,
        llm_client: Optional[Any] = None,
        approval_callback: Optional[ApprovalCallback] = None,
        progress_callback: Optional[ProgressCallback] = None,
    ):
        self.name = name
        self.description = description
        self.llm_client = llm_client
        self.approval_callback = approval_callback
        self.progress_callback = progress_callback

    @abstractmethod
    async def execute(self, task: str, **kwargs) -> Any:
        """执行技能"""
        pass

    async def request_approval(
        self, action: str, context: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        请求人工审批

        Returns:
            bool: 是否批准
        """
        if context is None:
            context = {}
        if self.approval_callback:
            return await self.approval_callback(action, context)
        return True  # 默认批准

    async def report_progress(self, message: str, current: int = 0, total: int = 100):
        """汇报进度"""
        if self.progress_callback:
            await self.progress_callback(message, current, total)

    def to_tool_definition(self) -> "ToolDefinition":
        """
        将 Skill 转换为 MCP ToolDefinition (2026 Skill-Tool Unification)

        自动从 execute 方法签名生成 JSON Schema。
        """
        import inspect
        from council.mcp.tool_search import ToolDefinition, ToolCategory

        # 获取 execute 方法的签名
        sig = inspect.signature(self.execute)

        # 构建 Schema
        properties = {}
        required = []

        for name, param in sig.parameters.items():
            if name == "self":
                continue

            param_schema = {"type": "string"}  # 默认

            # 简单类型推断
            if param.annotation is int:
                param_schema = {"type": "integer"}
            elif param.annotation is float:
                param_schema = {"type": "number"}
            elif param.annotation is bool:
                param_schema = {"type": "boolean"}
            elif (
                param.annotation is list
                or getattr(param.annotation, "__origin__", None) is list
            ):
                param_schema = {"type": "array", "items": {"type": "string"}}
            elif (
                param.annotation is dict
                or getattr(param.annotation, "__origin__", None) is dict
            ):
                param_schema = {"type": "object"}

            properties[name] = param_schema

            if param.default == inspect.Parameter.empty:
                required.append(name)

        schema = {"type": "object", "properties": properties, "required": required}

        return ToolDefinition(
            name=self.name,
            description=self.description,
            category=ToolCategory.CODE,  # 默认为代码类
            schema=schema,
            keywords=["skill", self.name.lower()],
            token_cost=500,  # Skill 通常较重
            defer_loading=True,
        )

    def __str__(self):
        return f"Skill(name={self.name})"
