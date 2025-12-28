"""
Protocol Schema - 结构化 Agent 通信协议

定义 Agent 间通信的 Pydantic 模型，用于替代自然语言交换。
实现 2025 Best Practice: Protocol-First Communication.

Token Savings: ~70% reduction compared to verbose NL.
"""

from enum import Enum, IntEnum
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator


class VoteEnum(IntEnum):
    """
    投票决策枚举 (整数编码节省 Token)
    
    0=REJECT, 1=APPROVE, 2=APPROVE_WITH_CHANGES, 3=HOLD
    """
    REJECT = 0
    APPROVE = 1
    APPROVE_WITH_CHANGES = 2
    HOLD = 3
    
    def to_legacy(self) -> str:
        """转换为旧版字符串格式 (向后兼容)"""
        mapping = {
            0: "reject",
            1: "approve",
            2: "approve_with_changes",
            3: "hold",
        }
        return mapping[self.value]


class RiskCategory(str, Enum):
    """
    风险类别枚举
    
    使用缩写字符串，便于 LLM 输出。
    """
    SECURITY = "sec"        # 安全风险 (注入、泄露、认证)
    PERFORMANCE = "perf"    # 性能风险 (延迟、内存、并发)
    MAINTENANCE = "maint"   # 维护风险 (可读性、复杂度)
    ARCHITECTURE = "arch"   # 架构风险 (耦合、扩展性)
    DATA = "data"           # 数据风险 (一致性、完整性)
    NONE = "none"           # 无风险


class MinimalVote(BaseModel):
    """
    极简投票结构 (Zero-Waste Protocol)
    
    Agent 输出此 JSON 而非冗长文本。
    
    Example:
        {"vote": 1, "confidence": 0.9, "risks": ["sec"], "blocking_reason": null}
    """
    vote: VoteEnum = Field(description="0=REJECT, 1=APPROVE, 2=APPROVE_WITH_CHANGES, 3=HOLD")
    confidence: float = Field(ge=0.0, le=1.0, description="置信度 0.0-1.0")
    risks: List[RiskCategory] = Field(default_factory=list, description="风险类别列表")
    blocking_reason: Optional[str] = Field(
        None, 
        max_length=100, 
        description="拒绝/暂缓原因 (最多100字符)"
    )
    
    @field_validator("confidence")
    @classmethod
    def round_confidence(cls, v: float) -> float:
        """保留两位小数"""
        return round(v, 2)
    
    def to_legacy_dict(self) -> dict:
        """转换为旧版 Vote 兼容格式"""
        return {
            "decision": self.vote.to_legacy(),
            "confidence": self.confidence,
            "rationale": self.blocking_reason or "",
        }


class MinimalThinkResult(BaseModel):
    """
    极简思考结果 (Zero-Waste Protocol)
    
    限制字段长度，强制 Agent 精炼输出。
    
    Example:
        {
            "summary": "设计合理，但缓存策略需要优化",
            "concerns": ["缓存失效风险", "并发锁争用"],
            "suggestions": ["使用 Redis Cluster"],
            "confidence": 0.85
        }
    """
    summary: str = Field(max_length=200, description="摘要 (最多200字符)")
    concerns: List[str] = Field(
        default_factory=list, 
        max_length=5,
        description="担忧列表 (每项最多50字符)"
    )
    suggestions: List[str] = Field(
        default_factory=list,
        max_length=5,
        description="建议列表 (每项最多50字符)"
    )
    confidence: float = Field(ge=0.0, le=1.0, description="置信度 0.0-1.0")
    perspective: Optional[str] = Field(None, max_length=20, description="视角标签")
    
    @field_validator("concerns", "suggestions", mode="before")
    @classmethod
    def truncate_lists(cls, v):
        """限制列表长度"""
        if isinstance(v, list):
            return [str(item)[:50] for item in v[:5]]
        return v
    
    def to_legacy_dict(self) -> dict:
        """转换为旧版 ThinkResult 兼容格式"""
        return {
            "analysis": self.summary,
            "concerns": self.concerns,
            "suggestions": self.suggestions,
            "confidence": self.confidence,
            "context": {"perspective": self.perspective} if self.perspective else {},
        }


class DebateMessage(BaseModel):
    """
    辩论消息 (用于 Agent 间通信)
    
    比自然语言对话节省 ~80% Token。
    """
    agent: str = Field(max_length=30, description="发言 Agent 名称")
    message_type: str = Field(
        default="comment",
        pattern="^(vote|comment|question|response)$",
        description="消息类型"
    )
    content: str = Field(max_length=150, description="消息内容 (最多150字符)")
    references: List[int] = Field(
        default_factory=list,
        description="引用的消息 ID 列表"
    )


# 导出
__all__ = [
    "VoteEnum",
    "RiskCategory",
    "MinimalVote",
    "MinimalThinkResult",
    "DebateMessage",
]
