"""
BaseAgent - 智能体基类
所有专家角色的抽象基类，定义统一接口
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from enum import Enum
from datetime import datetime


class VoteDecision(Enum):
    """投票决策枚举"""

    APPROVE = "approve"
    APPROVE_WITH_CHANGES = "approve_with_changes"
    HOLD = "hold"
    REJECT = "reject"


@dataclass
class Vote:
    """投票结果"""

    agent_name: str
    decision: VoteDecision
    confidence: float  # 0.0 - 1.0
    rationale: str
    timestamp: datetime = field(default_factory=datetime.now)
    suggested_changes: Optional[List[str]] = None


@dataclass
class ThinkResult:
    """思考结果"""

    analysis: str
    concerns: List[str] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)
    confidence: float = 0.5
    context: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ExecuteResult:
    """执行结果"""

    success: bool
    output: str
    changes_made: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    rollback_info: Optional[Dict[str, Any]] = None


class BaseAgent(ABC):
    """
    智能体基类

    所有专家角色必须继承此类并实现核心方法：
    - think(): 分析任务并产出思考结果
    - vote(): 对提案进行投票
    - execute(): 执行具体任务
    """

    def __init__(
        self,
        name: str,
        system_prompt: str,
        model: str = "gemini-2.0-flash",
    ):
        """
        初始化智能体

        Args:
            name: 智能体名称
            system_prompt: 系统提示词（定义角色人格）
            model: 使用的 LLM 模型
        """
        self.name = name
        self.system_prompt = system_prompt
        self.model = model
        self.history: List[Dict[str, Any]] = []

        # API key detection
        import os

        self._has_gemini = bool(os.environ.get("GEMINI_API_KEY"))
        self._has_openai = bool(os.environ.get("OPENAI_API_KEY"))

    def _call_llm(self, prompt: str, system_override: Optional[str] = None) -> str:
        """
        调用 LLM API

        Args:
            prompt: 用户提示词
            system_override: 可选的系统提示词覆盖

        Returns:
            LLM 响应文本
        """
        import os

        system = system_override or self.system_prompt

        # Try Gemini first
        if self._has_gemini:
            try:
                import google.generativeai as genai

                genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))
                model = genai.GenerativeModel(
                    self.model,
                    system_instruction=system,
                )
                response = model.generate_content(prompt)
                return response.text
            except Exception:
                # Fall through to OpenAI
                pass

        # Fallback to OpenAI
        if self._has_openai:
            try:
                from openai import OpenAI

                client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
                response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": system},
                        {"role": "user", "content": prompt},
                    ],
                )
                return response.choices[0].message.content
            except Exception:
                pass

        # No API available - return stub response
        return f"[STUB] Agent {self.name} received: {prompt[:100]}..."

    def _has_llm(self) -> bool:
        """检查是否有可用的 LLM API"""
        return self._has_gemini or self._has_openai

    @abstractmethod
    def think(self, task: str, context: Optional[Dict[str, Any]] = None) -> ThinkResult:
        """
        分析任务并产出思考结果

        Args:
            task: 任务描述
            context: 可选的上下文信息

        Returns:
            ThinkResult: 思考结果
        """
        pass

    @abstractmethod
    def vote(self, proposal: str, context: Optional[Dict[str, Any]] = None) -> Vote:
        """
        对提案进行投票

        Args:
            proposal: 提案内容
            context: 可选的上下文信息（如其他智能体的意见）

        Returns:
            Vote: 投票结果
        """
        pass

    @abstractmethod
    def execute(
        self, task: str, plan: Optional[Dict[str, Any]] = None
    ) -> ExecuteResult:
        """
        执行具体任务

        Args:
            task: 任务描述
            plan: 可选的执行计划

        Returns:
            ExecuteResult: 执行结果
        """
        pass

    def add_to_history(self, event: Dict[str, Any]) -> None:
        """添加事件到历史记录"""
        event["timestamp"] = datetime.now().isoformat()
        event["agent"] = self.name
        self.history.append(event)

    def get_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """获取最近的历史记录"""
        return self.history[-limit:]

    def clear_history(self) -> None:
        """清空历史记录"""
        self.history = []

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name='{self.name}', model='{self.model}')"


# 导出
__all__ = [
    "BaseAgent",
    "Vote",
    "VoteDecision",
    "ThinkResult",
    "ExecuteResult",
]
