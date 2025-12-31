"""
Task Classifier - 任务分类器 (December 2025 Update)

基于任务描述自动分类，推荐合适的模型。

2025年12月 模型阵容:
- Claude 4.5 Opus    (80.9% SWE-bench, 复杂任务)
- Claude 4.5 Sonnet  (77.2% SWE-bench, 日常编码)
- GPT 5.2 Codex      (规划，安全审计)
- Gemini 3 Pro       (1M 上下文，全库审计)
- Gemini 3 Flash     (78% SWE-bench, 3x 速度, 1/4 成本)
"""

from dataclasses import dataclass
from typing import Dict, List
from enum import Enum


class TaskType(Enum):
    """任务类型"""

    PLANNING = "planning"
    CODING = "coding"
    REVIEW = "review"
    DEBUGGING = "debugging"
    DOCUMENTATION = "documentation"
    REFACTORING = "refactoring"
    TESTING = "testing"
    SECURITY = "security"
    GENERAL = "general"


class RecommendedModel(Enum):
    """2025年12月 推荐模型"""

    # Claude 4.5
    CLAUDE_OPUS = "claude-4.5-opus"
    CLAUDE_SONNET = "claude-4.5-sonnet"
    # OpenAI
    GPT_CODEX = "gpt-5.2-codex"
    # Google Gemini 3
    GEMINI_PRO = "gemini-3-pro"
    GEMINI_FLASH = "gemini-3-flash"


@dataclass
class ModelSpec:
    """模型规格"""

    name: str
    swe_bench: float  # SWE-bench 分数
    context_window: int  # 上下文窗口 (tokens)
    relative_cost: float  # 相对成本 (1.0 = 基准)
    latency: str  # low/medium/high


# 2025年12月 模型规格 (已验证)
MODEL_SPECS: Dict[RecommendedModel, ModelSpec] = {
    RecommendedModel.CLAUDE_OPUS: ModelSpec(
        name="Claude 4.5 Opus",
        swe_bench=80.9,
        context_window=200_000,
        relative_cost=4.0,
        latency="high",
    ),
    RecommendedModel.CLAUDE_SONNET: ModelSpec(
        name="Claude 4.5 Sonnet",
        swe_bench=77.2,
        context_window=200_000,
        relative_cost=1.0,
        latency="low",
    ),
    RecommendedModel.GPT_CODEX: ModelSpec(
        name="GPT 5.2 Codex",
        swe_bench=78.0,  # SOTA on Terminal-Bench
        context_window=200_000,
        relative_cost=2.0,
        latency="medium",
    ),
    RecommendedModel.GEMINI_PRO: ModelSpec(
        name="Gemini 3 Pro",
        swe_bench=75.0,
        context_window=1_000_000,  # 1M tokens!
        relative_cost=4.0,
        latency="medium",
    ),
    RecommendedModel.GEMINI_FLASH: ModelSpec(
        name="Gemini 3 Flash",
        swe_bench=78.0,
        context_window=1_000_000,  # 1M tokens!
        relative_cost=1.0,  # 1/4 of Pro
        latency="low",  # 3x faster
    ),
}


@dataclass
class ClassificationResult:
    """分类结果"""

    task_type: TaskType
    confidence: float
    recommended_model: RecommendedModel
    fallback_model: RecommendedModel
    reason: str
    matched_keywords: List[str]


class TaskClassifier:
    """
    任务分类器 - 2025年12月更新

    基于官方验证数据的最佳分工:
    - 规划/架构 → GPT 5.2 Codex
    - 日常编码 → Claude 4.5 Sonnet
    - 复杂重构 → Claude 4.5 Opus
    - 全库审计 → Gemini 3 Pro
    - 快速任务 → Gemini 3 Flash
    - 安全审计 → GPT 5.2 Codex
    """

    TASK_PATTERNS: Dict[TaskType, List[str]] = {
        TaskType.PLANNING: [
            "设计",
            "架构",
            "方案",
            "规划",
            "plan",
            "design",
            "蓝图",
            "需求",
            "prd",
            "系统设计",
            "技术选型",
        ],
        TaskType.CODING: [
            "实现",
            "编写",
            "代码",
            "implement",
            "code",
            "write",
            "开发",
            "编码",
            "创建",
            "添加",
            "新增",
            "函数",
        ],
        TaskType.REVIEW: ["审查", "检查", "review", "audit", "审核"],
        TaskType.DEBUGGING: ["调试", "修复", "bug", "fix", "debug", "排查", "错误"],
        TaskType.DOCUMENTATION: ["文档", "说明", "doc", "readme", "注释"],
        TaskType.REFACTORING: ["重构", "优化", "refactor", "重写", "改进", "性能"],
        TaskType.TESTING: ["测试", "test", "单元测试", "tdd", "覆盖率"],
        TaskType.SECURITY: ["安全", "security", "漏洞", "vulnerability", "渗透"],
    }

    # 2025年12月 最佳分工映射
    MODEL_MAPPING: Dict[TaskType, RecommendedModel] = {
        TaskType.PLANNING: RecommendedModel.GPT_CODEX,
        TaskType.CODING: RecommendedModel.CLAUDE_SONNET,
        TaskType.REVIEW: RecommendedModel.GEMINI_PRO,
        TaskType.DEBUGGING: RecommendedModel.CLAUDE_SONNET,
        TaskType.DOCUMENTATION: RecommendedModel.CLAUDE_SONNET,
        TaskType.REFACTORING: RecommendedModel.CLAUDE_OPUS,
        TaskType.TESTING: RecommendedModel.GEMINI_FLASH,
        TaskType.SECURITY: RecommendedModel.GPT_CODEX,
        TaskType.GENERAL: RecommendedModel.CLAUDE_SONNET,
    }

    # 备选模型
    FALLBACK_MAPPING: Dict[TaskType, RecommendedModel] = {
        TaskType.PLANNING: RecommendedModel.CLAUDE_OPUS,
        TaskType.CODING: RecommendedModel.GEMINI_FLASH,
        TaskType.REVIEW: RecommendedModel.CLAUDE_OPUS,
        TaskType.DEBUGGING: RecommendedModel.GEMINI_FLASH,
        TaskType.DOCUMENTATION: RecommendedModel.GEMINI_FLASH,
        TaskType.REFACTORING: RecommendedModel.GPT_CODEX,
        TaskType.TESTING: RecommendedModel.CLAUDE_SONNET,
        TaskType.SECURITY: RecommendedModel.CLAUDE_OPUS,
        TaskType.GENERAL: RecommendedModel.GEMINI_FLASH,
    }

    MODEL_REASONS: Dict[RecommendedModel, str] = {
        RecommendedModel.CLAUDE_OPUS: "Claude 4.5 Opus: 80.9% SWE-bench 最高分，复杂任务首选",
        RecommendedModel.CLAUDE_SONNET: "Claude 4.5 Sonnet: 速度与质量平衡，日常编码推荐",
        RecommendedModel.GPT_CODEX: "GPT 5.2 Codex: 深度推理，规划与安全审计专精",
        RecommendedModel.GEMINI_PRO: "Gemini 3 Pro: 1M 上下文，全库审计首选",
        RecommendedModel.GEMINI_FLASH: "Gemini 3 Flash: 3x 速度，1/4 成本，高频任务首选",
    }

    def __init__(self, cost_sensitive: bool = False):
        """
        初始化分类器

        Args:
            cost_sensitive: 是否优先考虑成本
        """
        self.cost_sensitive = cost_sensitive

    def classify(self, task: str) -> ClassificationResult:
        """分类任务并推荐模型"""
        scores: Dict[TaskType, tuple[float, List[str]]] = {}
        task_lower = task.lower()

        for task_type, keywords in self.TASK_PATTERNS.items():
            matched = [kw for kw in keywords if kw.lower() in task_lower]
            if matched:
                score = len(matched) / len(keywords)
                scores[task_type] = (score, matched)

        if not scores:
            return ClassificationResult(
                task_type=TaskType.GENERAL,
                confidence=0.5,
                recommended_model=RecommendedModel.CLAUDE_SONNET,
                fallback_model=RecommendedModel.GEMINI_FLASH,
                reason="未匹配，使用通用处理",
                matched_keywords=[],
            )

        best_type = max(scores.keys(), key=lambda t: scores[t][0])
        best_score, matched_keywords = scores[best_type]

        recommended = self.MODEL_MAPPING[best_type]
        fallback = self.FALLBACK_MAPPING[best_type]

        # 成本敏感模式: 优先使用便宜模型
        if self.cost_sensitive:
            spec = MODEL_SPECS[recommended]
            if spec.relative_cost > 2.0:
                recommended, fallback = fallback, recommended

        return ClassificationResult(
            task_type=best_type,
            confidence=min(best_score * 1.5, 1.0),
            recommended_model=recommended,
            fallback_model=fallback,
            reason=self.MODEL_REASONS[recommended],
            matched_keywords=matched_keywords,
        )

    def recommend_model(self, task: str) -> RecommendedModel:
        """快速获取推荐模型"""
        return self.classify(task).recommended_model

    def get_model_spec(self, model: RecommendedModel) -> ModelSpec:
        """获取模型规格"""
        return MODEL_SPECS[model]

    def explain(self, result: ClassificationResult) -> str:
        """解释分类结果"""
        spec = MODEL_SPECS[result.recommended_model]
        return f"""
任务类型: {result.task_type.value}
推荐模型: {spec.name}
SWE-bench: {spec.swe_bench}%
上下文: {spec.context_window:,} tokens
原因: {result.reason}
""".strip()


__all__ = [
    "TaskClassifier",
    "ClassificationResult",
    "TaskType",
    "RecommendedModel",
    "ModelSpec",
    "MODEL_SPECS",
]
