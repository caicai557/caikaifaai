# Model Router - 多模型智能路由
"""
基于 2026 多模型路由最佳实践:
- 根据任务类型自动选择最优模型
- 成本/延迟权衡配置
- 回退模型支持
- 性能追踪与自适应路由 (2026 新增)
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from datetime import datetime
import logging

from council.orchestration.task_classifier import (
    TaskClassifier,
    TaskType,
    RecommendedModel,
    MODEL_SPECS,
)

logger = logging.getLogger(__name__)


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


@dataclass
class ModelPerformanceStats:
    """
    模型性能统计 (2026 新增)

    Attributes:
        model_name: 模型名称
        total_calls: 总调用次数
        successful_calls: 成功调用次数
        total_latency_ms: 总延迟(毫秒)
        last_updated: 最后更新时间
    """

    model_name: str
    total_calls: int = 0
    successful_calls: int = 0
    total_latency_ms: float = 0.0
    last_updated: datetime = field(default_factory=datetime.now)
    recent_latencies: List[float] = field(default_factory=list)  # 最近10次延迟

    @property
    def success_rate(self) -> float:
        """成功率"""
        if self.total_calls == 0:
            return 1.0  # 无历史数据时假设100%
        return self.successful_calls / self.total_calls

    @property
    def avg_latency_ms(self) -> float:
        """平均延迟"""
        if self.total_calls == 0:
            return 0.0
        return self.total_latency_ms / self.total_calls

    @property
    def recent_avg_latency_ms(self) -> float:
        """最近平均延迟"""
        if not self.recent_latencies:
            return 0.0
        return sum(self.recent_latencies) / len(self.recent_latencies)

    def is_degraded(self, success_threshold: float = 0.8, latency_threshold_ms: float = 5000) -> bool:
        """
        判断模型是否处于降级状态

        Args:
            success_threshold: 成功率阈值
            latency_threshold_ms: 延迟阈值(毫秒)

        Returns:
            bool: 是否应该降级
        """
        # 至少有5次调用才判断
        if self.total_calls < 5:
            return False

        # 成功率过低
        if self.success_rate < success_threshold:
            return True

        # 最近延迟过高
        if self.recent_avg_latency_ms > latency_threshold_ms:
            return True

        return False


class ModelRouter:
    """
    多模型智能路由器 (2026 增强版)

    新增功能:
    - 性能追踪: 记录每个模型的成功率和延迟
    - 自适应路由: 根据历史性能动态调整模型选择
    - 自动降级: 当模型性能下降时自动切换到备选
    """

    def __init__(
        self,
        cost_sensitive: bool = False,
        prefer_speed: bool = False,
        custom_rules: Optional[Dict[str, RecommendedModel]] = None,
        enable_adaptive: bool = True,
        success_threshold: float = 0.8,
        latency_threshold_ms: float = 5000,
    ):
        self.cost_sensitive = cost_sensitive
        self.prefer_speed = prefer_speed
        self.custom_rules = custom_rules or {}
        self._classifier = TaskClassifier(cost_sensitive=cost_sensitive)

        # 2026 新增: 性能追踪
        self.enable_adaptive = enable_adaptive
        self.success_threshold = success_threshold
        self.latency_threshold_ms = latency_threshold_ms

        # 性能统计存储
        self._performance_stats: Dict[str, ModelPerformanceStats] = {}

        # 降级模型映射
        self._fallback_chain: Dict[str, str] = {
            "claude-4.5-opus": "claude-4.5-sonnet",
            "claude-4.5-sonnet": "gemini-3-flash",
            "gpt-5.2-codex": "claude-4.5-sonnet",
            "gemini-3-pro": "gemini-3-flash",
            "gemini-3-flash": "gpt-4o-mini",
        }

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

    # ========== 2026 新增: 性能追踪与自适应路由 ==========

    def update_stats(
        self,
        model_name: str,
        latency_ms: float,
        success: bool,
    ) -> None:
        """
        更新模型性能统计

        Args:
            model_name: 模型名称
            latency_ms: 延迟(毫秒)
            success: 是否成功
        """
        if model_name not in self._performance_stats:
            self._performance_stats[model_name] = ModelPerformanceStats(model_name=model_name)

        stats = self._performance_stats[model_name]
        stats.total_calls += 1
        stats.total_latency_ms += latency_ms
        stats.last_updated = datetime.now()

        if success:
            stats.successful_calls += 1

        # 记录最近延迟(保留最近10次)
        stats.recent_latencies.append(latency_ms)
        if len(stats.recent_latencies) > 10:
            stats.recent_latencies.pop(0)

        logger.debug(
            f"ModelRouter stats updated: {model_name} "
            f"success_rate={stats.success_rate:.2%}, "
            f"avg_latency={stats.avg_latency_ms:.0f}ms"
        )

    def get_stats(self, model_name: str) -> Optional[ModelPerformanceStats]:
        """获取模型性能统计"""
        return self._performance_stats.get(model_name)

    def get_all_stats(self) -> Dict[str, ModelPerformanceStats]:
        """获取所有模型性能统计"""
        return self._performance_stats.copy()

    def _should_degrade(self, model_name: str) -> bool:
        """
        判断是否应该降级模型

        Args:
            model_name: 模型名称

        Returns:
            bool: 是否应该降级
        """
        if not self.enable_adaptive:
            return False

        stats = self._performance_stats.get(model_name)
        if stats is None:
            return False

        return stats.is_degraded(
            success_threshold=self.success_threshold,
            latency_threshold_ms=self.latency_threshold_ms,
        )

    def _get_fallback_model(self, model_name: str) -> Optional[str]:
        """获取降级模型"""
        return self._fallback_chain.get(model_name)

    async def route_adaptive(self, task: str) -> ModelConfig:
        """
        自适应路由 (2026 新增)

        根据历史性能动态选择模型,如果主模型性能下降则自动切换到备选。

        Args:
            task: 任务描述

        Returns:
            ModelConfig: 选择的模型配置
        """
        # 先获取基础路由结果
        base_config = await self.route(task)

        if not self.enable_adaptive:
            return base_config

        # 检查是否需要降级
        model_name = base_config.model_name
        if self._should_degrade(model_name):
            fallback = self._get_fallback_model(model_name)
            if fallback:
                logger.warning(
                    f"Model {model_name} degraded, falling back to {fallback}"
                )
                # 构造降级配置
                return ModelConfig(
                    model_name=fallback,
                    api_provider=ROUTER_MODEL_CONFIGS.get(fallback, {}).get("provider", "unknown"),
                    context_window=ROUTER_MODEL_CONFIGS.get(fallback, {}).get("context", 100000),
                    relative_cost=ROUTER_MODEL_CONFIGS.get(fallback, {}).get("cost", 1.0),
                    latency=ROUTER_MODEL_CONFIGS.get(fallback, {}).get("latency", "low"),
                    task_type=base_config.task_type,
                    confidence=base_config.confidence * 0.8,
                )

        return base_config

    def reset_stats(self, model_name: Optional[str] = None) -> None:
        """
        重置性能统计

        Args:
            model_name: 模型名称,为None时重置所有
        """
        if model_name:
            if model_name in self._performance_stats:
                del self._performance_stats[model_name]
        else:
            self._performance_stats.clear()

    def estimate_tokens(self, text: str) -> int:
        """
        估算文本 Token 数量 (2026 新增)

        使用简单的字符计数估算,约4个字符=1个Token

        Args:
            text: 输入文本

        Returns:
            int: 估算的Token数量
        """
        # 简单估算: 英文约4字符/token, 中文约2字符/token
        # 混合文本取平均
        return len(text) // 3

    def get_model_for_text(self, text: str, task_type: TaskType = TaskType.GENERAL) -> ModelConfig:
        """
        根据文本长度自动选择模型 (2026 新增)

        Args:
            text: 输入文本
            task_type: 任务类型

        Returns:
            ModelConfig: 推荐的模型配置
        """
        tokens = self.estimate_tokens(text)
        return self.get_model_for_context_size(tokens)


__all__ = [
    "ModelRouter",
    "ModelConfig",
    "RoutingResult",
    "ModelPerformanceStats",
    "ROUTER_MODEL_CONFIGS",
]
