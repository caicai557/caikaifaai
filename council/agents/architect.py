"""
Architect - 架构师智能体
负责顶层设计、架构评审、风险识别
"""

from typing import Optional, Dict, Any, List
from council.agents.base_agent import (
    BaseAgent, Vote, VoteDecision, ThinkResult, ExecuteResult
)


ARCHITECT_SYSTEM_PROMPT = """你是一名资深软件架构师，拥有 20 年的系统设计经验。

## 核心职责
1. **顶层设计**: 评估系统架构的合理性和可扩展性
2. **风险识别**: 识别技术债务、性能瓶颈、安全隐患
3. **方案评审**: 对设计提案进行深度分析

## 决策原则
- 优先考虑系统的长期可维护性
- 权衡复杂度与收益
- 关注接口设计和模块边界
- 识别潜在的技术债务

## 输出格式
始终使用结构化的分析框架：
1. 架构影响分析
2. 风险评估 (高/中/低)
3. 改进建议
4. 替代方案 (如有)

## 禁止行为
- 不做没有依据的判断
- 不忽视安全问题
- 不推荐过度设计
"""


class Architect(BaseAgent):
    """
    架构师智能体
    
    专注于系统顶层设计和架构评审
    """
    
    def __init__(self, model: str = "gemini-2.0-flash"):
        super().__init__(
            name="Architect",
            system_prompt=ARCHITECT_SYSTEM_PROMPT,
            model=model,
        )
    
    def think(self, task: str, context: Optional[Dict[str, Any]] = None) -> ThinkResult:
        """
        从架构角度分析任务
        """
        # 架构师关注点
        concerns = []
        suggestions = []
        
        # 模拟架构分析（实际实现需要调用 LLM）
        analysis = f"[Architect Analysis] 任务: {task}\n"
        analysis += "正在从系统架构角度进行分析...\n"
        
        # 记录到历史
        self.add_to_history({
            "action": "think",
            "task": task,
            "context": context,
        })
        
        return ThinkResult(
            analysis=analysis,
            concerns=concerns,
            suggestions=suggestions,
            confidence=0.8,
            context={"perspective": "architecture"},
        )
    
    def vote(self, proposal: str, context: Optional[Dict[str, Any]] = None) -> Vote:
        """
        对提案进行架构评审投票
        """
        # 模拟投票逻辑（实际实现需要调用 LLM）
        self.add_to_history({
            "action": "vote",
            "proposal": proposal,
            "context": context,
        })
        
        return Vote(
            agent_name=self.name,
            decision=VoteDecision.APPROVE_WITH_CHANGES,
            confidence=0.85,
            rationale="架构设计合理，但建议增加接口抽象层",
            suggested_changes=["添加接口抽象层", "增加错误处理机制"],
        )
    
    def execute(self, task: str, plan: Optional[Dict[str, Any]] = None) -> ExecuteResult:
        """
        执行架构相关任务（如生成架构文档）
        """
        self.add_to_history({
            "action": "execute",
            "task": task,
            "plan": plan,
        })
        
        return ExecuteResult(
            success=True,
            output=f"架构师已完成任务: {task}",
            changes_made=["生成架构设计文档"],
        )
    
    def review_design(self, design_doc: str) -> Dict[str, Any]:
        """
        专门的设计评审方法
        
        Args:
            design_doc: 设计文档内容
            
        Returns:
            评审结果
        """
        return {
            "reviewer": self.name,
            "status": "reviewed",
            "concerns": [],
            "suggestions": [],
            "approval": True,
        }


__all__ = ["Architect", "ARCHITECT_SYSTEM_PROMPT"]
