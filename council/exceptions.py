"""
Council Exceptions - 统一异常层级

提供层级式异常用于:
- 精确错误处理
- 清晰错误信息
- 易于调试
"""


class CouncilError(Exception):
    """Base exception for all council errors"""

    def __init__(self, message: str, details: dict = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}


# ============================================================
# Agent Errors
# ============================================================


class AgentError(CouncilError):
    """Agent execution error"""

    pass


class AgentNotFoundError(AgentError):
    """Agent not found in registry"""

    def __init__(self, agent_name: str):
        super().__init__(
            f"Agent '{agent_name}' not found in registry", {"agent_name": agent_name}
        )


class AgentExecutionError(AgentError):
    """Agent failed to execute task"""

    def __init__(self, agent_name: str, task: str, reason: str):
        super().__init__(
            f"Agent '{agent_name}' failed: {reason}",
            {"agent_name": agent_name, "task": task, "reason": reason},
        )


# ============================================================
# Delegation Errors
# ============================================================


class DelegationError(CouncilError):
    """Delegation chain error"""

    pass


class MaxDepthExceededError(DelegationError):
    """Delegation depth limit exceeded"""

    def __init__(self, current_depth: int, max_depth: int):
        super().__init__(
            f"Delegation depth {current_depth} exceeds max {max_depth}",
            {"current_depth": current_depth, "max_depth": max_depth},
        )


class CircularDelegationError(DelegationError):
    """Circular delegation detected"""

    def __init__(self, chain: list):
        super().__init__(
            f"Circular delegation detected: {' -> '.join(chain)}", {"chain": chain}
        )


# ============================================================
# Memory Errors
# ============================================================


class MemoryError(CouncilError):
    """Memory/storage error"""

    pass


class VectorStoreError(MemoryError):
    """Vector database error"""

    pass


class CheckpointError(MemoryError):
    """Checkpoint save/load error"""

    pass


# ============================================================
# LLM Errors
# ============================================================


class LLMError(CouncilError):
    """LLM API error"""

    pass


class StreamTimeoutError(LLMError):
    """Streaming response timeout"""

    def __init__(self, timeout: float):
        super().__init__(f"Stream timed out after {timeout}s", {"timeout": timeout})


class ModelNotAvailableError(LLMError):
    """Requested model not available"""

    def __init__(self, model: str):
        super().__init__(f"Model '{model}' is not available", {"model": model})


__all__ = [
    # Base
    "CouncilError",
    # Agent
    "AgentError",
    "AgentNotFoundError",
    "AgentExecutionError",
    # Delegation
    "DelegationError",
    "MaxDepthExceededError",
    "CircularDelegationError",
    # Memory
    "MemoryError",
    "VectorStoreError",
    "CheckpointError",
    # LLM
    "LLMError",
    "StreamTimeoutError",
    "ModelNotAvailableError",
]
