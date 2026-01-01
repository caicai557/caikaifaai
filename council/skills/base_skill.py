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

    def __str__(self):
        return f"Skill(name={self.name})"
