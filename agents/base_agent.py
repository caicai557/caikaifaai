"""
BaseAgent - 智能体基类
所有专家角色的抽象基类，定义统一接口
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any, Callable
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
        allow_delegation: bool = False,
        allowed_agents: Optional[List[str]] = None,
        max_delegation_depth: int = 3,
        governance_gateway: Optional["GovernanceGateway"] = None,
    ):
        """
        初始化智能体
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
        self.stream_callback: Optional[Callable[[str], None]] = None

        # API key detection
        import os

        self._has_gemini = bool(os.environ.get("GEMINI_API_KEY"))
        self._has_openai = bool(os.environ.get("OPENAI_API_KEY"))
        
        # Initialize Cache Manager
        if self._has_gemini:
            from council.context.gemini_cache import GeminiCacheManager
            self.cache_manager = GeminiCacheManager()
        else:
            self.cache_manager = None

    def set_stream_callback(self, callback: Optional[Callable[[str], None]]):
        """设置流式输出回调"""
        self.stream_callback = callback

    def _call_llm(self, prompt: str, system_override: Optional[str] = None) -> str:
        """
        调用 LLM API (Public Interface)
        """
        # 如果设置了回调，使用流式调用
        if self.stream_callback:
            full_text = ""
            for chunk in self._call_llm_stream(prompt, system_override):
                self.stream_callback(chunk)
                full_text += chunk
            return full_text
        
        return self._generate_response(prompt, system_override)

    def _generate_response(self, prompt: str, system_override: Optional[str] = None) -> str:
        """
        生成响应 (Internal, Non-streaming)
        """
        import os

        system = system_override or self.system_prompt

        # Try Gemini first
        if self._has_gemini:
            try:
                import google.generativeai as genai

                genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))
                
                # 1. Try to use Caching for System Prompt + Context
                cache_name = f"cache_{self.name}_{hash(system)}"
                cached_id = self.cache_manager.create(cache_name, system, ttl_hours=1)
                
                if cached_id:
                    # Use Cached Model
                    response_text = self.cache_manager.generate_with_cache(cached_id, prompt)
                    if response_text:
                        return response_text
                
                # Fallback to standard generation
                model = genai.GenerativeModel(
                    self.model,
                    system_instruction=system,
                )
                response = model.generate_content(prompt)
                return response.text
            except Exception as e:
                # Fall through to OpenAI
                print(f"Gemini Error: {e}")
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

    def _call_llm_stream(self, prompt: str, system_override: Optional[str] = None):
        """
        [2025 Best Practice] 流式调用 LLM
        Yields: chunks of text
        """
        import os
        system = system_override or self.system_prompt

        if self._has_gemini:
            try:
                import google.generativeai as genai
                genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))

                # 1. Try Caching
                cache_name = f"cache_{self.name}_{hash(system)}"
                cached_id = self.cache_manager.create(cache_name, system, ttl_hours=1)
                
                if cached_id:
                    yield from self.cache_manager.generate_with_cache_stream(cached_id, prompt)
                    return

                # 2. Standard Streaming
                model = genai.GenerativeModel(self.model, system_instruction=system)
                response = model.generate_content(prompt, stream=True)
                for chunk in response:
                    if chunk.text:
                        yield chunk.text
                return
            except Exception as e:
                # print(f"Gemini Stream Error: {e}")
                pass
        
        # Fallback to non-streaming if stream fails or not supported
        yield self._generate_response(prompt, system_override)

    def _has_llm(self) -> bool:
        """检查是否有可用的 LLM API"""
        return self._has_gemini or self._has_openai

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
        schema_class: type,
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
        import json
        from pydantic import ValidationError

        # 生成 JSON Schema 指令
        schema_example = schema_class.model_json_schema()
        json_instruction = f"""
Respond ONLY with valid JSON matching this schema (no markdown, no explanation):
{json.dumps(schema_example, indent=2, ensure_ascii=False)}

Example format:
{json.dumps(self._generate_example(schema_class), ensure_ascii=False)}
"""
        enhanced_prompt = f"{prompt}\n\n{json_instruction}"

        # 调用 LLM
        response = self._call_llm(enhanced_prompt, system_override)

        # 尝试解析 JSON
        try:
            # 清理响应 (移除可能的 markdown 包装)
            cleaned = self._clean_json_response(response)
            data = json.loads(cleaned)
            return schema_class(**data)
        except (json.JSONDecodeError, ValidationError) as e:
            # 回退: 返回默认实例并记录错误
            self.add_to_history(
                {
                    "action": "structured_call_fallback",
                    "error": str(e),
                    "raw_response": response[:200],
                }
            )
            # 返回带默认值的实例
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
