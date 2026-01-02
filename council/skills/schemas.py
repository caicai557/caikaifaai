"""
Skill Output Schemas - 结构化输出模型

定义 LLM 生成内容的 Pydantic 模型，用于 structured_completion() 验证。
"""

from typing import Optional, List
from pydantic import BaseModel, Field


class GeneratedCodeOutput(BaseModel):
    """代码生成输出"""

    code: str = Field(..., description="生成的代码")
    language: str = Field("python", description="编程语言")
    explanation: Optional[str] = Field(None, description="代码说明")


class AnalysisCodeOutput(BaseModel):
    """数据分析代码输出"""

    code: str = Field(..., description="Python 分析脚本")
    imports: List[str] = Field(default_factory=list, description="需要的导入")
    explanation: Optional[str] = Field(None, description="分析步骤说明")


class SummaryOutput(BaseModel):
    """研究总结输出"""

    summary: str = Field(..., description="核心总结")
    key_points: List[str] = Field(default_factory=list, description="关键要点")
    confidence: float = Field(0.8, ge=0.0, le=1.0, description="置信度")


class CodeFixOutput(BaseModel):
    """代码修复输出"""

    fixed_code: str = Field(..., description="修复后的代码")
    changes_made: List[str] = Field(default_factory=list, description="所做的修改")
    root_cause: Optional[str] = Field(None, description="问题根因分析")


__all__ = [
    "GeneratedCodeOutput",
    "AnalysisCodeOutput",
    "SummaryOutput",
    "CodeFixOutput",
]
