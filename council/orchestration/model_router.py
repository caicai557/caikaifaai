# Model Router - 多模型智能路由
"""
基于 2025 多模型路由最佳实践:
- 根据任务类型自动选择最优模型
- 成本/延迟权衡配置
- 回退模型支持
"""

from dataclasses import dataclass
from typing import Optional, List, Dict, Any

from council.orchestration.task_classifier import (
    TaskClassifier,
    TaskType,
    RecommendedModel,
    MODEL_SPECS,
)


@dataclass
class ModelConfig:
    """模型配置"""
    model_name: str
    api_provider: str
    context_window: int
    relative_cost: float
    latency: str
    task_type: TaskType
    confidence: float


@dataclass
class RoutingResult:
    """路由结果（带回退）"""
    primary: ModelConfig
    fallback: ModelConfig
    reason: str
    matched_keywords: List[str]


PROVIDER_MAPPING: Dict[RecommendedModel, str] = {
    RecommendedModel.CLAUDE_OPUS: "anthropic",
    RecommendedModel.CLAUDE_SONNET: "anthropic",
    RecommendedModel.GPT_CODEX: "openai",
    RecommendedModel.GEMINI_PRO: "google",
    RecommendedModel.GEMINI_FLASH: "google",
}

ROUTER_MODEL_CONFIGS: Dict[str, Dict[str, Any]] = {
    "claude-4.5-opus": {"provider": "anthropic", "context": 200_000, "cost": 4.0, "latency": "high"},
    "claude-4.5-sonnet": {"provider": "anthropic", "context": 200_000, "cost": 1.0, "latency": "low"},
    "gpt-5.2-codex": {"provider": "openai", "context": 200_000, "cost": 2.0, "latency": "medium"},
    "gemini-3-pro": {"provider": "google", "context": 1_000_000, "cost": 4.0, "latency": "medium"},
    "gemini-3-flash": {"provider": "google", "context": 1_000_000, "cost": 1.0, "latency": "low"},
}


class ModelRouter:
    """多模型智能路由器"""

    def __init__(self, cost_sensitive: bool = False, prefer_speed: bool = False, custom_rules: Optional[Dict[str, RecommendedModel]] = None):
        self.cost_sensitive = cost_sensitive
        self.prefer_speed = prefer_speed
        self.custom_rules = custom_rules or {}
        self._classifier = TaskClassifier(cost_sensitive=cost_sensitive)

    def _model_to_config(self, model: RecommendedModel, task_type: TaskType, confidence: float) -> ModelConfig:
        spec = MODEL_SPECS[model]
        return ModelConfig(
            model_name=model.value,
            api_provider=PROVIDER_MAPPING[model],
            context_window=spec.context_window,
            relative_cost=spec.relative_cost,
            latency=spec.latency,
            task_type=task_type,
            confidence=confidence,
        )

    async def route(self, task: str) -> ModelConfig:
        task_lower = task.lower()
        for keyword, model in self.custom_rules.items():
            if keyword.lower() in task_lower:
                return self._model_to_config(model, TaskType.GENERAL, 1.0)
        result = self._classifier.classify(task)
        if self.prefer_speed:
            spec = MODEL_SPECS[result.recommended_model]
            if spec.latency == "high":
                result.recommended_model = result.fallback_model
        return self._model_to_config(result.recommended_model, result.task_type, result.confidence)

    async def route_with_fallback(self, task: str) -> RoutingResult:
        result = self._classifier.classify(task)
        primary = self._model_to_config(result.recommended_model, result.task_type, result.confidence)
        fallback = self._model_to_config(result.fallback_model, result.task_type, result.confidence * 0.8)
        return RoutingResult(primary=primary, fallback=fallback, reason=result.reason, matched_keywords=result.matched_keywords)

    async def route_batch(self, tasks: List[str]) -> List[ModelConfig]:
        return [await self.route(task) for task in tasks]

    def get_model_for_context_size(self, context_tokens: int) -> ModelConfig:
        if context_tokens > 200_000:
            model = RecommendedModel.GEMINI_PRO if not self.cost_sensitive else RecommendedModel.GEMINI_FLASH
            return self._model_to_config(model, TaskType.GENERAL, 0.9)
        if context_tokens > 50_000:
            return self._model_to_config(RecommendedModel.CLAUDE_SONNET, TaskType.GENERAL, 0.9)
        return self._model_to_config(RecommendedModel.GEMINI_FLASH, TaskType.GENERAL, 0.9)


__all__ = ["ModelRouter", "ModelConfig", "RoutingResult", "ROUTER_MODEL_CONFIGS"]
