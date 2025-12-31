"""
Token Tracker - Token使用追踪

参考: OpenTelemetry + LangSmith 最佳实践
功能: 追踪LLM调用的Token使用量和成本
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional
from datetime import datetime
from enum import Enum
import json


class ModelProvider(Enum):
    """模型提供商"""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GOOGLE = "google"
    OTHER = "other"


# 2025年12月 模型定价 (每1M tokens, USD)
MODEL_PRICING = {
    # OpenAI
    "gpt-5.2-codex": {"input": 15.0, "output": 60.0},
    "gpt-4o": {"input": 2.5, "output": 10.0},
    
    # Anthropic
    "claude-4.5-opus": {"input": 15.0, "output": 75.0},
    "claude-4.5-sonnet": {"input": 3.0, "output": 15.0},
    "claude-3.5-sonnet": {"input": 3.0, "output": 15.0},
    
    # Google
    "gemini-3-pro": {"input": 1.25, "output": 5.0},
    "gemini-3-flash": {"input": 0.075, "output": 0.30},
    "gemini-2.0-flash": {"input": 0.075, "output": 0.30},
    
    # Default
    "default": {"input": 1.0, "output": 4.0},
}


@dataclass
class TokenUsage:
    """单次Token使用记录"""
    prompt_tokens: int
    completion_tokens: int
    model: str
    agent_name: str = ""
    action: str = ""
    timestamp: datetime = field(default_factory=datetime.now)
    
    @property
    def total_tokens(self) -> int:
        return self.prompt_tokens + self.completion_tokens
    
    @property
    def cost_usd(self) -> float:
        """计算成本 (USD)"""
        pricing = MODEL_PRICING.get(self.model, MODEL_PRICING["default"])
        input_cost = (self.prompt_tokens / 1_000_000) * pricing["input"]
        output_cost = (self.completion_tokens / 1_000_000) * pricing["output"]
        return input_cost + output_cost
    
    def to_dict(self) -> Dict:
        return {
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
            "total_tokens": self.total_tokens,
            "model": self.model,
            "agent": self.agent_name,
            "action": self.action,
            "cost_usd": round(self.cost_usd, 6),
            "timestamp": self.timestamp.isoformat(),
        }


@dataclass
class TokenTracker:
    """Token使用追踪器"""
    session_id: str = ""
    usages: List[TokenUsage] = field(default_factory=list)
    
    def record(
        self,
        prompt_tokens: int,
        completion_tokens: int,
        model: str,
        agent_name: str = "",
        action: str = ""
    ) -> TokenUsage:
        """记录Token使用"""
        usage = TokenUsage(
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            model=model,
            agent_name=agent_name,
            action=action,
        )
        self.usages.append(usage)
        return usage
    
    def total_tokens(self) -> int:
        """总Token数"""
        return sum(u.total_tokens for u in self.usages)
    
    def total_cost(self) -> float:
        """总成本 (USD)"""
        return sum(u.cost_usd for u in self.usages)
    
    def by_agent(self) -> Dict[str, Dict]:
        """按Agent统计"""
        stats = {}
        for u in self.usages:
            name = u.agent_name or "unknown"
            if name not in stats:
                stats[name] = {"tokens": 0, "cost": 0.0, "calls": 0}
            stats[name]["tokens"] += u.total_tokens
            stats[name]["cost"] += u.cost_usd
            stats[name]["calls"] += 1
        return stats
    
    def by_model(self) -> Dict[str, Dict]:
        """按模型统计"""
        stats = {}
        for u in self.usages:
            if u.model not in stats:
                stats[u.model] = {"tokens": 0, "cost": 0.0, "calls": 0}
            stats[u.model]["tokens"] += u.total_tokens
            stats[u.model]["cost"] += u.cost_usd
            stats[u.model]["calls"] += 1
        return stats
    
    def to_metrics(self) -> Dict:
        """导出指标"""
        return {
            "session_id": self.session_id,
            "total_tokens": self.total_tokens(),
            "total_cost_usd": round(self.total_cost(), 4),
            "total_calls": len(self.usages),
            "by_agent": self.by_agent(),
            "by_model": self.by_model(),
        }
    
    def to_json(self) -> str:
        """导出JSON"""
        return json.dumps(self.to_metrics(), indent=2, ensure_ascii=False)
    
    def reset(self):
        """重置追踪器"""
        self.usages.clear()


# 全局追踪器实例
_global_tracker: Optional[TokenTracker] = None


def get_tracker(session_id: str = "default") -> TokenTracker:
    """获取全局追踪器"""
    global _global_tracker
    if _global_tracker is None:
        _global_tracker = TokenTracker(session_id=session_id)
    return _global_tracker


def record_usage(
    prompt_tokens: int,
    completion_tokens: int,
    model: str,
    agent_name: str = "",
    action: str = ""
) -> TokenUsage:
    """便捷函数：记录Token使用"""
    return get_tracker().record(
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        model=model,
        agent_name=agent_name,
        action=action,
    )


# 导出
__all__ = [
    "TokenUsage",
    "TokenTracker",
    "ModelProvider",
    "MODEL_PRICING",
    "get_tracker",
    "record_usage",
]
