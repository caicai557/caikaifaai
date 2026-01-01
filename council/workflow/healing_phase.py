"""
Healing Phase - 自愈校验与共识裁决阶段

使用 Wald 序列分析算法评估共识概率 π，动态决定提交或人工介入。
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime
from enum import Enum


class HealingAction(Enum):
    """自愈动作"""
    AUTO_COMMIT = "auto_commit"  # π ≥ α
    HITL_REQUEST = "hitl_request"  # π ≤ β
    CONTINUE = "continue"  # 继续迭代


@dataclass
class HealingAttempt:
    """自愈尝试记录"""
    attempt_number: int
    traceback: str
    fix_applied: str
    success: bool
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class ConsensusResult:
    """共识结果"""
    pi: float  # 共识概率
    action: HealingAction
    votes: Dict[str, str]
    rationale: str


class SelfHealingLoop:
    """
    自愈循环
    
    - 分析 Traceback 自动修复
    - 最大 3 次重试
    - Wald SPRT 动态终止
    """
    max_attempts: int = 3
    alpha: float = 0.95  # 提交阈值
    beta: float = 0.05   # 终止阈值
    
    def __init__(
        self,
        max_attempts: int = 3,
        alpha: float = 0.95,
        beta: float = 0.05,
        llm_client: Optional[Any] = None
    ):
        self.max_attempts = max_attempts
        self.alpha = alpha
        self.beta = beta
        self.llm_client = llm_client
        self.attempts: List[HealingAttempt] = []
    
    def analyze_traceback(self, traceback: str) -> Dict[str, Any]:
        """
        分析错误堆栈
        
        Args:
            traceback: 错误堆栈
            
        Returns:
            分析结果
        """
        # TODO: 调用 LLM 分析
        return {
            "error_type": "unknown",
            "file": "",
            "line": 0,
            "suggested_fix": "",
        }
    
    def attempt_fix(self, analysis: Dict[str, Any]) -> HealingAttempt:
        """
        尝试修复
        
        Args:
            analysis: 分析结果
            
        Returns:
            修复尝试记录
        """
        attempt = HealingAttempt(
            attempt_number=len(self.attempts) + 1,
            traceback=str(analysis.get("error_type", "")),
            fix_applied=analysis.get("suggested_fix", ""),
            success=False,
        )
        self.attempts.append(attempt)
        return attempt
    
    def evaluate_consensus(self, votes: Dict[str, str]) -> ConsensusResult:
        """
        评估共识 (Wald SPRT)
        
        Args:
            votes: Agent 投票 {"agent_name": "approve/reject"}
            
        Returns:
            共识结果
        """
        approves = sum(1 for v in votes.values() if v == "approve")
        total = len(votes)
        pi = approves / total if total > 0 else 0.5
        
        if pi >= self.alpha:
            action = HealingAction.AUTO_COMMIT
            rationale = f"π={pi:.2f} ≥ α={self.alpha}, 自动提交"
        elif pi <= self.beta:
            action = HealingAction.HITL_REQUEST
            rationale = f"π={pi:.2f} ≤ β={self.beta}, 请求人工介入"
        else:
            action = HealingAction.CONTINUE
            rationale = f"π={pi:.2f}, 继续迭代"
        
        return ConsensusResult(
            pi=pi,
            action=action,
            votes=votes,
            rationale=rationale,
        )
    
    def should_continue(self) -> bool:
        """是否继续尝试"""
        return len(self.attempts) < self.max_attempts


__all__ = [
    "SelfHealingLoop",
    "HealingAction",
    "HealingAttempt",
    "ConsensusResult",
]
