"""
BaseAgent - 智能体基类
所有专家角色的抽象基类，定义统一接口
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any, Type
from enum import Enum
from datetime import datetime
import os

from pydantic import BaseModel

from council.core.llm_client import LLMClient, default_client

# 默认模型 - 2025 December 配置
# vertex_ai/ 使用 Google Cloud ADC 凭证登录
# anthropic/ 使用 Anthropic API Key
# openai/ 使用 OpenAI API Key


# 模型配置 (2025 最佳实践: 差异化模型分配)
class ModelConfig:
    """
    Agent 专用模型配置 (账户 Auto 认证)

    使用策略:
    - Claude: 深度推理、规划、架构设计
    - Codex: 代码审计、安全分析
    - Gemini: ⚠️ 大范围扫描读取或长上下文必须使用
      - gemini-3-flash: 高频迭代 (80%调用, 成本敏感)
      - gemini-3-pro: 长上下文研究 (2M tokens)
    """

    # Claude 4.5 Opus - 高级推理模型 (规划、架构)
    CLAUDE_OPUS = "claude-4.5-opus"

    # Claude 4.5 Sonnet - 平衡模型 (可选替代)
    CLAUDE_SONNET = "claude-4.5-sonnet"

    # Codex 5.2 - 代码审计模型
    CODEX = "codex-5.2"

    # Gemini 3 Flash - 高频迭代模型 (成本敏感, 80%调用)
    GEMINI_FLASH = "gemini-3-flash"

    # Gemini 3 Pro - 网络研究模型 (长上下文)
    GEMINI_PRO = "gemini-3-pro"

    # 默认模型
    DEFAULT = GEMINI_FLASH


# 各 Agent 默认模型
MODEL_ORCHESTRATOR = ModelConfig.CLAUDE_OPUS
MODEL_ARCHITECT = ModelConfig.CLAUDE_OPUS
MODEL_CODER = ModelConfig.GEMINI_FLASH
MODEL_SECURITY_AUDITOR = ModelConfig.CODEX
MODEL_WEB_SURFER = ModelConfig.GEMINI_PRO

# 兼容旧代码
DEFAULT_MODEL = ModelConfig.DEFAULT


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
        model: str = DEFAULT_MODEL,
        allow_delegation: bool = False,
        allowed_agents: Optional[List[str]] = None,
        max_delegation_depth: int = 3,
        governance_gateway: Optional["GovernanceGateway"] = None,
        llm_client: Optional[LLMClient] = None,
        memory_aggregator=None,
        context_manager=None,
    ):
        """
        初始化智能体

        Args:
            name: 智能体名称
            system_prompt: 系统提示词（定义角色人格）
            model: 使用的 LLM 模型
            allow_delegation: 是否允许委托任务给其他 Agent
            allowed_agents: 允许委托的 Agent 名称列表 (None = 允许所有)
            max_delegation_depth: 最大委托链深度
            governance_gateway: 可选的治理网关 (关键决策审批)
            memory_aggregator: 可选的记忆聚合器 (MemoryAggregator 实例)
            context_manager: 可选的上下文管理器 (ContextManager 实例)
        """
        self.name = name
        self.system_prompt = system_prompt
        self.model = model
        self.allow_delegation = allow_delegation
        self.allowed_agents = allowed_agents or []
        self.max_delegation_depth = max_delegation_depth
        self.history: List[Dict[str, Any]] = []
        self._current_delegation_depth = 0
        self.governance_gateway = governance_gateway

        # 2025 Advanced: Memory and Context integration
        self.memory_aggregator = memory_aggregator
        self.context_manager = context_manager

        # 2025 Core Upgrade: 使用统一的 LLMClient
        self.llm_client = llm_client or default_client
        self._has_gemini = bool(
            os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
        )
        self._has_openai = bool(os.environ.get("OPENAI_API_KEY"))

    def _call_llm(self, prompt: str, system_override: Optional[str] = None) -> str:
        """
        调用 LLM API (通过统一客户端)

        Args:
            prompt: 用户提示词
            system_override: 可选的系统提示词覆盖

        Returns:
            LLM 响应文本
        """
        messages = []
        if system_override or self.system_prompt:
            messages.append(
                {"role": "system", "content": system_override or self.system_prompt}
            )

        messages.append({"role": "user", "content": prompt})

        return self.llm_client.completion(messages=messages, model=self.model)

    def _has_llm(self) -> bool:
        """检查是否有可用的 LLM API"""
        return self._has_gemini or self._has_openai

    def _query_memory(self, query: str, max_chars: int = 2000) -> str:
        """
        查询记忆聚合器获取相关上下文

        Args:
            query: 查询文本
            max_chars: 最大字符数

        Returns:
            格式化的记忆上下文，无记忆时返回空字符串
        """
        if not self.memory_aggregator:
            return ""

        try:
            return self.memory_aggregator.get_context_for_llm(query, max_chars)
        except Exception:
            return ""

    def _record_to_memory(
        self,
        content: str,
        memory_type: str = "short_term",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Optional[str]:
        """
        记录重要信息到记忆系统

        Args:
            content: 要记录的内容
            memory_type: 记忆类型 (short_term/long_term/working)
            metadata: 可选元数据

        Returns:
            记忆 ID，失败时返回 None
        """
        if not self.memory_aggregator:
            return None

        try:
            meta = metadata or {}
            meta["agent"] = self.name
            return self.memory_aggregator.remember(content, memory_type, meta)
        except Exception:
            return None

    def request_decision_approval(
        self,
        decision_type: "DecisionType",
        description: str,
        affected_resources: List[str],
        rationale: str,
        council_decision: Optional[Dict[str, Any]] = None,
        requestor: Optional[str] = None,
        timeout_seconds: int = 300,
    ) -> bool:
        """
        请求关键决策审批
        """
        from council.governance.gateway import GovernanceGateway, DecisionType

        if not isinstance(decision_type, DecisionType):
            raise ValueError("decision_type must be a DecisionType")

        if self.governance_gateway is None:
            self.governance_gateway = GovernanceGateway()

        if not self.governance_gateway.requires_decision_approval(decision_type):
            return True

        request = self.governance_gateway.create_decision_request(
            decision_type=decision_type,
            description=description,
            affected_resources=affected_resources,
            rationale=rationale,
            council_decision=council_decision,
            requestor=requestor or self.name,
        )
        approved = self.governance_gateway.wait_for_approval(
            request,
            timeout_seconds=timeout_seconds,
        )
        self.add_to_history(
            {
                "action": "decision_approval",
                "decision_type": decision_type.value,
                "approved": approved,
                "request_id": request.request_id,
            }
        )
        return approved

    def _call_llm_structured(
        self,
        prompt: str,
        schema_class: Type[BaseModel],
        system_override: Optional[str] = None,
    ) -> Any:
        """
        [2025 Best Practice] 调用 LLM 并期望结构化 JSON 输出

        Args:
            prompt: 用户提示词
            schema_class: Pydantic 模型类 (用于验证)
            system_override: 可选的系统提示词覆盖

        Returns:
            已验证的 Pydantic 模型实例
        """
        messages = []
        if system_override or self.system_prompt:
            messages.append(
                {"role": "system", "content": system_override or self.system_prompt}
            )

        messages.append({"role": "user", "content": prompt})

        try:
            return self.llm_client.structured_completion(
                messages=messages, response_model=schema_class, model=self.model
            )
        except Exception as e:
            # 回退: 返回默认实例并记录错误
            self.add_to_history(
                {
                    "action": "structured_call_fallback",
                    "error": str(e),
                }
            )
            return self._create_default_instance(schema_class)

    def _clean_json_response(self, response: str) -> str:
        """清理 LLM 响应中的非 JSON 内容"""
        import re

        # 移除 markdown 代码块
        if "```json" in response:
            match = re.search(r"```json\s*(.*?)\s*```", response, re.DOTALL)
            if match:
                return match.group(1)
        if "```" in response:
            match = re.search(r"```\s*(.*?)\s*```", response, re.DOTALL)
            if match:
                return match.group(1)
        # 尝试找到 JSON 对象
        match = re.search(r"\{.*\}", response, re.DOTALL)
        if match:
            return match.group(0)
        return response

    def _generate_example(self, schema_class: type) -> dict:
        """生成 schema 的示例 JSON"""

        # 简单的示例生成
        if schema_class.__name__ == "MinimalVote":
            return {
                "vote": 1,
                "confidence": 0.8,
                "risks": ["sec"],
                "blocking_reason": None,
            }
        elif schema_class.__name__ == "MinimalThinkResult":
            return {
                "summary": "Analysis summary",
                "concerns": ["Issue 1"],
                "suggestions": ["Fix 1"],
                "confidence": 0.7,
            }
        else:
            return {}

    def _create_default_instance(self, schema_class: type) -> Any:
        """创建带默认值的 schema 实例"""
        if schema_class.__name__ == "MinimalVote":
            from council.protocol.schema import MinimalVote, VoteEnum

            return MinimalVote(vote=VoteEnum.HOLD, confidence=0.5)
        elif schema_class.__name__ == "MinimalThinkResult":
            from council.protocol.schema import MinimalThinkResult

            return MinimalThinkResult(summary="Parse failed", confidence=0.3)
        else:
            return schema_class()

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
