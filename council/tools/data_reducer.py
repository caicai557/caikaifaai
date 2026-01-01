"""
Data Reducer - 数据降维器

核心功能:
1. 执行层数据降维，仅返回高信号摘要
2. 10MB 日志 → ≤2KB 摘要
3. PII 数据自动过滤
4. 异常检测与提取

规则:
- 最大输出 2000 字符
- 保留关键统计信息
- 移除冗余内容
"""

from dataclasses import dataclass
from typing import List, Optional, Dict, Any
from enum import Enum
import re


class AnomalyType(Enum):
    """异常类型"""

    ERROR = "error"
    WARNING = "warning"
    CRITICAL = "critical"
    PERFORMANCE = "performance"
    SECURITY = "security"


@dataclass
class Anomaly:
    """异常信息"""

    type: AnomalyType
    description: str
    line_number: Optional[int] = None
    context: Optional[str] = None
    severity: int = 1  # 1-10


class DataReducer:
    """
    数据降维器 - 仅返回高信号摘要

    核心规则:
    - 10MB 日志 → ≤2KB 摘要
    - 10,000 行数据 → 关键统计 + 异常
    - PII 数据自动过滤
    """

    # PII 模式
    PII_PATTERNS: List[tuple] = [
        (r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b", "[EMAIL]"),
        (r"\b\d{3}[-.]?\d{3}[-.]?\d{4}\b", "[PHONE]"),
        (r"\b\d{3}-\d{2}-\d{4}\b", "[SSN]"),
        (r"\b(?:4[0-9]{12}(?:[0-9]{3})?|5[1-5][0-9]{14})\b", "[CREDIT_CARD]"),
        (r"\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b", "[IP_ADDRESS]"),
        (r"(?i)password\s*[=:]\s*\S+", "[PASSWORD_REDACTED]"),
        (r"(?i)api[_-]?key\s*[=:]\s*\S+", "[API_KEY_REDACTED]"),
        (r"(?i)secret\s*[=:]\s*\S+", "[SECRET_REDACTED]"),
        (r"(?i)token\s*[=:]\s*\S+", "[TOKEN_REDACTED]"),
    ]

    # 异常检测模式
    ANOMALY_PATTERNS = [
        (r"(?i)\berror\b", AnomalyType.ERROR),
        (r"(?i)\bwarning\b", AnomalyType.WARNING),
        (r"(?i)\bcritical\b", AnomalyType.CRITICAL),
        (r"(?i)\bfailed\b", AnomalyType.ERROR),
        (r"(?i)\bexception\b", AnomalyType.ERROR),
        (r"(?i)\btimeout\b", AnomalyType.PERFORMANCE),
        (r"(?i)\bunauthorized\b", AnomalyType.SECURITY),
        (r"(?i)\bdenied\b", AnomalyType.SECURITY),
    ]

    def __init__(
        self,
        max_chars: int = 2000,
        filter_pii: bool = True,
        extract_stats: bool = True,
    ):
        self.max_chars = max_chars
        self.filter_pii = filter_pii
        self.extract_stats = extract_stats

        # 编译正则表达式
        self._pii_compiled = [
            (re.compile(pattern), replacement)
            for pattern, replacement in self.PII_PATTERNS
        ]
        self._anomaly_compiled = [
            (re.compile(pattern), anomaly_type)
            for pattern, anomaly_type in self.ANOMALY_PATTERNS
        ]

    def reduce(
        self,
        stdout: str,
        stderr: str = "",
        max_tokens: Optional[int] = None,
    ) -> str:
        """
        压缩输出为摘要

        Args:
            stdout: 标准输出
            stderr: 标准错误
            max_tokens: 最大 token 数 (可选)

        Returns:
            压缩后的摘要 (≤2000 字符)
        """
        max_chars = max_tokens or self.max_chars

        # Step 1: 过滤 PII
        if self.filter_pii:
            stdout = self._filter_pii(stdout)
            stderr = self._filter_pii(stderr)

        # Step 2: 提取关键信息
        combined = self._combine_output(stdout, stderr)

        # Step 3: 如果足够短，直接返回
        if len(combined) <= max_chars:
            return combined

        # Step 4: 智能压缩
        summary = self._smart_compress(combined, max_chars)

        return summary

    def extract_anomalies(self, data: str) -> List[Anomaly]:
        """
        提取关键异常信息

        Args:
            data: 要分析的数据

        Returns:
            检测到的异常列表
        """
        anomalies = []
        lines = data.split("\n")

        for i, line in enumerate(lines, 1):
            for pattern, anomaly_type in self._anomaly_compiled:
                if pattern.search(line):
                    # 提取上下文
                    context_start = max(0, i - 2)
                    context_end = min(len(lines), i + 2)
                    context = "\n".join(lines[context_start:context_end])

                    anomaly = Anomaly(
                        type=anomaly_type,
                        description=line.strip()[:200],  # 限制长度
                        line_number=i,
                        context=context[:500],
                        severity=self._calculate_severity(anomaly_type),
                    )
                    anomalies.append(anomaly)

        # 去重并排序
        unique_anomalies = self._deduplicate_anomalies(anomalies)
        return sorted(unique_anomalies, key=lambda a: a.severity, reverse=True)[:20]

    def extract_statistics(self, data: str) -> Dict[str, Any]:
        """
        提取统计信息

        Args:
            data: 要分析的数据

        Returns:
            统计信息字典
        """
        lines = data.split("\n")

        stats = {
            "total_lines": len(lines),
            "total_chars": len(data),
            "error_count": 0,
            "warning_count": 0,
            "unique_patterns": set(),
        }

        for line in lines:
            if re.search(r"(?i)\berror\b", line):
                stats["error_count"] += 1
            if re.search(r"(?i)\bwarning\b", line):
                stats["warning_count"] += 1

        # 转换 set 为 list 以便 JSON 序列化
        stats["unique_patterns"] = list(stats["unique_patterns"])

        return stats

    def _filter_pii(self, text: str) -> str:
        """过滤 PII 数据"""
        for pattern, replacement in self._pii_compiled:
            text = pattern.sub(replacement, text)
        return text

    def _combine_output(self, stdout: str, stderr: str) -> str:
        """合并输出"""
        # 优化: 如果只有 stdout 且没有 stderr，直接返回 stdout (避免 header 增加 token)
        if stdout and not stderr:
            return stdout.strip()

        parts = []

        if stdout.strip():
            parts.append(f"=== STDOUT ===\n{stdout.strip()}")

        if stderr.strip():
            parts.append(f"=== STDERR ===\n{stderr.strip()}")

        return "\n\n".join(parts) if parts else "(无输出)"

    def _smart_compress(self, text: str, max_chars: int) -> str:
        """智能压缩"""
        lines = text.split("\n")

        # 策略 1: 保留首尾 + 关键行
        important_lines = []

        # 保留前 20 行
        important_lines.extend(lines[:20])

        # 保留包含关键词的行
        keywords = ["error", "warning", "failed", "success", "result", "total", "count"]
        for line in lines[20:-20]:
            if any(kw in line.lower() for kw in keywords):
                important_lines.append(line)

        # 保留后 10 行
        important_lines.extend(lines[-10:])

        # 组装摘要
        summary_text = "\n".join(important_lines)

        # 如果还是太长，强制截断
        if len(summary_text) > max_chars:
            truncated = summary_text[: max_chars - 100]
            summary_text = f"{truncated}\n\n... [截断，原始 {len(text)} 字符]"

        # 添加统计信息
        if self.extract_stats:
            stats = self.extract_statistics(text)
            stats_line = f"\n📊 统计: {stats['total_lines']} 行, {stats['error_count']} 错误, {stats['warning_count']} 警告"
            if len(summary_text) + len(stats_line) <= max_chars:
                summary_text += stats_line

        return summary_text

    def _calculate_severity(self, anomaly_type: AnomalyType) -> int:
        """计算异常严重程度"""
        severity_map = {
            AnomalyType.CRITICAL: 10,
            AnomalyType.SECURITY: 9,
            AnomalyType.ERROR: 7,
            AnomalyType.WARNING: 4,
            AnomalyType.PERFORMANCE: 5,
        }
        return severity_map.get(anomaly_type, 1)

    def _deduplicate_anomalies(self, anomalies: List[Anomaly]) -> List[Anomaly]:
        """去重异常"""
        seen = set()
        unique = []

        for anomaly in anomalies:
            key = (anomaly.type, anomaly.description[:50])
            if key not in seen:
                seen.add(key)
                unique.append(anomaly)

        return unique


__all__ = ["DataReducer", "Anomaly", "AnomalyType"]
