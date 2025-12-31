"""
Protocol Schema - 结构化 Agent 通信协议

定义 Agent 间通信的 Pydantic 模型，用于替代自然语言交换。
实现 2025 Best Practice: Protocol-First Communication.

Token Savings: ~70% reduction compared to verbose NL.
"""

from enum import Enum, IntEnum
from typing import List, Optional, Dict, Any
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



class DevStatus(str, Enum):
    """
    开发状态枚举 (State Machine States) - EPCC 方法论
    """
    EXPLORING = "exploring"      # 🔍 探索理解
    ANALYZING = "analyzing"      # 📊 任务分析
    PLANNING = "planning"        # 📋 规划设计 (人工审批)
    CODING = "coding"            # 💻 TDD 编码
    TESTING = "testing"          # 🧪 验证测试
    HEALING = "healing"          # 🔧 自愈修复
    REVIEWING = "reviewing"      # 👀 Council 审查
    COMPLETED = "completed"      # ✅ 完成
    FAILED = "failed"            # ❌ 失败
    HUMAN_REQUIRED = "human_required"  # ⚠️ 需人工介入


class AgentOutput(BaseModel):
    """
    通用 Agent 输出包装器
    """
    agent_name: str
    content: str
    structured_data: Optional[dict] = None
    timestamp: float = Field(default_factory=lambda: __import__("time").time())


class Subtask(BaseModel):
    """
    子任务定义
    """
    id: int
    description: str
    status: str = "pending"  # pending, done, failed
    result: Optional[str] = None
    error: Optional[str] = None


class Plan(BaseModel):
    """
    开发计划
    """
    goal: str
    subtasks: List[Subtask] = []
    risks: List[str] = []


class CouncilState(BaseModel):
    """
    Council 全局状态 (State Machine Context)
    
    所有 Agent 共享此状态对象。
    """
    task: str
    status: DevStatus = DevStatus.EXPLORING  # 从探索开始
    plan: Optional[Plan] = None
    current_subtask_index: int = 0
    code_files: dict[str, str] = Field(default_factory=dict, description="文件名 -> 内容")
    test_results: List[dict] = Field(default_factory=list)
    review_comments: List[str] = Field(default_factory=list)
    history: List[str] = Field(default_factory=list, description="操作日志")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="元数据 (如分类结果)")
    
    def log(self, message: str):
        """记录日志"""
        self.history.append(message)


# 导出
__all__ = [
    "VoteEnum",
    "RiskCategory",
    "MinimalVote",
    "MinimalThinkResult",
    "DebateMessage",
    "DevStatus",
    "AgentOutput",
    "Subtask",
    "Plan",
    "CouncilState",
]
