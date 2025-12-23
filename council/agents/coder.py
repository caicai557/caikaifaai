"""
Coder - 工程师智能体
负责代码实现、测试编写、功能开发
"""

from typing import Optional, Dict, Any, List
from council.agents.base_agent import (
    BaseAgent, Vote, VoteDecision, ThinkResult, ExecuteResult
)


CODER_SYSTEM_PROMPT = """你是一名高级软件工程师，专注于代码实现和测试。

## 核心职责
1. **代码实现**: 将设计转化为高质量代码
2. **测试编写**: TDD 驱动，确保覆盖率 ≥ 90%
3. **代码审查**: 识别代码质量问题

## 编码原则
- Small Diffs: 每次改动尽量小 (≤200 行)
- 防御性编程: 空值/异常/竞态必须处理
- 可读性优先: 代码是写给人看的
- 测试先行: 先写测试，后写实现

## 输出格式
1. 实现计划 (步骤列表)
2. 代码差异 (unified diff)
3. 验证命令 + 预期结果
4. 回滚步骤

## 禁止行为
- 不做无测试的实现
- 不引入大量新依赖
- 不做无依据的大重构
"""


class Coder(BaseAgent):
    """
    工程师智能体
    
    专注于代码实现和测试编写
    """
    
    def __init__(self, model: str = "gemini-2.0-flash"):
        super().__init__(
            name="Coder",
            system_prompt=CODER_SYSTEM_PROMPT,
            model=model,
        )
    
    def think(self, task: str, context: Optional[Dict[str, Any]] = None) -> ThinkResult:
        """
        从实现角度分析任务
        """
        analysis = f"[Coder Analysis] 任务: {task}\n"
        analysis += "正在分析实现方案...\n"
        
        self.add_to_history({
            "action": "think",
            "task": task,
            "context": context,
        })
        
        return ThinkResult(
            analysis=analysis,
            concerns=["需要确认测试覆盖率要求"],
            suggestions=["建议先编写单元测试"],
            confidence=0.85,
            context={"perspective": "implementation"},
        )
    
    def vote(self, proposal: str, context: Optional[Dict[str, Any]] = None) -> Vote:
        """
        对提案进行实现可行性投票
        """
        self.add_to_history({
            "action": "vote",
            "proposal": proposal,
            "context": context,
        })
        
        return Vote(
            agent_name=self.name,
            decision=VoteDecision.APPROVE,
            confidence=0.9,
            rationale="实现方案可行，符合 Small Diffs 原则",
        )
    
    def execute(self, task: str, plan: Optional[Dict[str, Any]] = None) -> ExecuteResult:
        """
        执行代码实现任务
        """
        self.add_to_history({
            "action": "execute",
            "task": task,
            "plan": plan,
        })
        
        return ExecuteResult(
            success=True,
            output=f"工程师已完成实现: {task}",
            changes_made=["实现核心功能", "添加单元测试"],
        )
    
    def generate_tests(self, spec: str) -> Dict[str, Any]:
        """
        生成测试代码
        
        Args:
            spec: 功能规格说明
            
        Returns:
            测试生成结果
        """
        return {
            "generator": self.name,
            "test_count": 0,
            "coverage_estimate": 0.0,
            "test_files": [],
        }
    
    def review_code(self, code: str) -> Dict[str, Any]:
        """
        代码审查
        
        Args:
            code: 待审查代码
            
        Returns:
            审查结果
        """
        return {
            "reviewer": self.name,
            "issues": [],
            "suggestions": [],
            "approval": True,
        }


__all__ = ["Coder", "CODER_SYSTEM_PROMPT"]
