"""
Delegation Manager - 委托管理器

管理 Agent 间的任务委托，包括:
- 委托链追踪
- 深度限制检查
- 递归保护
- 回溯支持

基于 CrewAI hierarchical 和 AutoGen GroupChat 模式设计。
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from datetime import datetime
from enum import Enum

from council.agents.base_agent import BaseAgent, ExecuteResult


class DelegationStatus(Enum):
    """委托状态"""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    SUCCESS = "success"
    FAILED = "failed"
    REJECTED = "rejected"


@dataclass
class DelegationRequest:
    """委托请求"""

    task: str
    from_agent: str
    to_agent: str
    depth: int
    created_at: datetime = field(default_factory=datetime.now)
    context: Dict[str, Any] = field(default_factory=dict)


@dataclass
class DelegationResult:
    """委托结果"""

    request: DelegationRequest
    status: DelegationStatus
    result: Optional[ExecuteResult] = None
    error: Optional[str] = None
    completed_at: Optional[datetime] = None


class DelegationError(Exception):
    """委托异常"""

    pass


class MaxDepthExceededError(DelegationError):
    """最大深度超限异常"""

    pass


class DelegationNotAllowedError(DelegationError):
    """不允许委托异常"""

    pass


class DelegationManager:
    """
    委托管理器

    核心功能:
    1. 执行委托并追踪委托链
    2. 防止无限递归
    3. 维护委托历史

    Usage:
        from council.orchestration import AgentRegistry, DelegationManager

        registry = AgentRegistry()
        registry.register(orchestrator, ["planning"])
        registry.register(coder, ["coding"])

        dm = DelegationManager(registry)
        result = dm.delegate(
            task="实现登录功能",
            from_agent=orchestrator,
            to_agent_name="coder"
        )
    """

    def __init__(
        self,
        registry: "AgentRegistry",
        global_max_depth: int = 5,
    ):
        """
        初始化委托管理器

        Args:
            registry: Agent 注册中心
            global_max_depth: 全局最大委托深度
        """

        self.registry = registry
        self.global_max_depth = global_max_depth

        # 委托链追踪
        self._current_chain: List[str] = []
        self._history: List[DelegationResult] = []

    def delegate(
        self,
        task: str,
        from_agent: BaseAgent,
        to_agent_name: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> DelegationResult:
        """
        执行委托

        Args:
            task: 任务描述
            from_agent: 发起委托的 Agent
            to_agent_name: 目标 Agent 名称
            context: 可选上下文

        Returns:
            DelegationResult

        Raises:
            MaxDepthExceededError: 超过最大深度
            DelegationNotAllowedError: 不允许委托
        """
        current_depth = len(self._current_chain)

        # 创建请求
        request = DelegationRequest(
            task=task,
            from_agent=from_agent.name,
            to_agent=to_agent_name,
            depth=current_depth + 1,
            context=context or {},
        )

        # 检查委托合法性
        can_delegate, reason = self.registry.can_delegate_to(from_agent, to_agent_name)
        if not can_delegate:
            result = DelegationResult(
                request=request,
                status=DelegationStatus.REJECTED,
                error=reason,
                completed_at=datetime.now(),
            )
            self._history.append(result)
            raise DelegationNotAllowedError(reason)

        # 检查深度限制
        max_depth = min(from_agent.max_delegation_depth, self.global_max_depth)
        if current_depth >= max_depth:
            result = DelegationResult(
                request=request,
                status=DelegationStatus.REJECTED,
                error=f"超过最大委托深度 ({current_depth} >= {max_depth})",
                completed_at=datetime.now(),
            )
            self._history.append(result)
            raise MaxDepthExceededError(f"Depth {current_depth} >= {max_depth}")

        # 检查循环委托
        if to_agent_name in self._current_chain:
            result = DelegationResult(
                request=request,
                status=DelegationStatus.REJECTED,
                error=f"检测到循环委托: {' -> '.join(self._current_chain)} -> {to_agent_name}",
                completed_at=datetime.now(),
            )
            self._history.append(result)
            raise DelegationError("Circular delegation detected")

        # 执行委托
        target_agent = self.registry.get(to_agent_name)
        if not target_agent:
            raise DelegationError(f"Agent '{to_agent_name}' not found")

        # 更新委托链
        self._current_chain.append(from_agent.name)
        target_agent._current_delegation_depth = current_depth + 1

        try:
            # 执行目标 Agent 的任务
            exec_result = target_agent.execute(task, plan=context)

            result = DelegationResult(
                request=request,
                status=DelegationStatus.SUCCESS
                if exec_result.success
                else DelegationStatus.FAILED,
                result=exec_result,
                completed_at=datetime.now(),
            )
        except Exception as e:
            result = DelegationResult(
                request=request,
                status=DelegationStatus.FAILED,
                error=str(e),
                completed_at=datetime.now(),
            )
        finally:
            # 恢复委托链
            self._current_chain.pop()
            target_agent._current_delegation_depth = 0

        self._history.append(result)
        return result

    def get_current_chain(self) -> List[str]:
        """获取当前委托链"""
        return list(self._current_chain)

    def get_history(self, limit: int = 10) -> List[DelegationResult]:
        """获取委托历史"""
        return self._history[-limit:]

    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        if not self._history:
            return {"total": 0, "success_rate": 0}

        success_count = sum(
            1 for r in self._history if r.status == DelegationStatus.SUCCESS
        )
        return {
            "total": len(self._history),
            "success": success_count,
            "failed": len(self._history) - success_count,
            "success_rate": round(success_count / len(self._history) * 100, 1),
        }


# 导出
__all__ = [
    "DelegationManager",
    "DelegationRequest",
    "DelegationResult",
    "DelegationStatus",
    "DelegationError",
    "MaxDepthExceededError",
    "DelegationNotAllowedError",
]
