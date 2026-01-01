"""
Parallel Execution - 并发执行模式

2026最佳实践: 群体智能 + 防止Groupthink

核心原理:
- 多个专家智能体同时针对同一指令独立生成方案
- 成员之间在生成初期互不可见 (防止群体思维)
- 配合 AAD (All-Agents Drafting) 全代理草拟
- 聚合阶段选优，显著提高答案多样性

典型场景:
- 复杂研究任务
- 多路径代码重构选型
- 架构设计方案对比
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Callable, Awaitable
from datetime import datetime
from enum import Enum
import asyncio

from council.agents.base_agent import ModelConfig


class AggregationStrategy(Enum):
    """聚合策略"""
    VOTE = "vote"           # 投票选优
    MERGE = "merge"         # 合并融合
    EXPERT = "expert"       # 专家裁决
    CONSENSUS = "consensus" # 共识评估


@dataclass
class AgentDraft:
    """Agent草案"""
    agent_id: str
    agent_role: str
    draft: str
    confidence: float = 0.0
    reasoning: str = ""
    created_at: datetime = field(default_factory=datetime.now)
    token_used: int = 0


@dataclass
class ParallelResult:
    """并发执行结果"""
    task: str
    drafts: List[AgentDraft]
    selected_draft: Optional[AgentDraft] = None
    aggregation_strategy: AggregationStrategy = AggregationStrategy.VOTE
    diversity_score: float = 0.0  # 方案多样性评分
    execution_time_ms: float = 0.0
    total_tokens: int = 0


class ParallelExecutor:
    """
    并发执行器 - 群体智能实现
    
    核心特性:
    1. 独立生成: 各Agent互不可见初始推理
    2. 防止Groupthink: 避免早期意见传染
    3. AAD模式: 全代理草拟后聚合
    4. 多样性评估: 量化方案差异
    
    使用示例:
        executor = ParallelExecutor()
        result = await executor.execute_parallel(
            task="重构用户认证模块",
            agents=["Architect", "Coder", "SecurityAuditor"]
        )
    """
    
    def __init__(
        self,
        llm_client: Optional[Any] = None,
        max_concurrent: int = 5,
        timeout: float = 60.0,
    ):
        self.llm_client = llm_client
        self.max_concurrent = max_concurrent
        self.timeout = timeout
        self._semaphore = asyncio.Semaphore(max_concurrent)
    
    async def execute_parallel(
        self,
        task: str,
        agents: List[str],
        strategy: AggregationStrategy = AggregationStrategy.VOTE,
    ) -> ParallelResult:
        """
        并发执行任务 - AAD模式
        
        Args:
            task: 任务描述
            agents: 参与的Agent列表
            strategy: 聚合策略
            
        Returns:
            ParallelResult: 包含所有草案和选优结果
        """
        start_time = datetime.now()
        
        # 阶段1: 全代理草拟 (AAD)
        drafts = await self._all_agents_drafting(task, agents)
        
        # 阶段2: 多样性评估
        diversity_score = self._calculate_diversity(drafts)
        
        # 阶段3: 聚合选优
        selected = await self._aggregate(drafts, strategy)
        
        execution_time = (datetime.now() - start_time).total_seconds() * 1000
        total_tokens = sum(d.token_used for d in drafts)
        
        return ParallelResult(
            task=task,
            drafts=drafts,
            selected_draft=selected,
            aggregation_strategy=strategy,
            diversity_score=diversity_score,
            execution_time_ms=execution_time,
            total_tokens=total_tokens,
        )
    
    async def _all_agents_drafting(
        self,
        task: str,
        agents: List[str]
    ) -> List[AgentDraft]:
        """
        阶段1: 全代理草拟 (AAD)
        
        每个Agent独立写出完整方案，互不可见
        """
        tasks = []
        for agent_id in agents:
            tasks.append(self._generate_draft(task, agent_id))
        
        # 并发执行，互不干扰
        drafts = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 过滤异常
        valid_drafts = [d for d in drafts if isinstance(d, AgentDraft)]
        return valid_drafts
    
    async def _generate_draft(self, task: str, agent_id: str) -> AgentDraft:
        """生成单个Agent草案"""
        async with self._semaphore:
            # 独立生成，无上下文污染
            prompt = f"""
作为 {agent_id}，请独立分析以下任务并给出完整方案：

## 任务
{task}

## 要求
1. 独立思考，不参考其他方案
2. 给出完整的解决方案
3. 说明推理过程
4. 评估置信度 (0-1)

## 输出格式
方案: [你的完整方案]
推理: [推理过程]
置信度: [0.0-1.0]
"""
            # 模拟LLM调用
            # 实际使用时替换为真实调用
            await asyncio.sleep(0.1)  # 模拟延迟
            
            return AgentDraft(
                agent_id=agent_id,
                agent_role=agent_id,
                draft=f"[{agent_id}的独立方案]: {task[:50]}...",
                confidence=0.8,
                reasoning=f"{agent_id}的独立推理过程",
                token_used=500,
            )
    
    def _calculate_diversity(self, drafts: List[AgentDraft]) -> float:
        """
        计算方案多样性评分
        
        多样性越高，说明探索空间越广
        """
        if len(drafts) < 2:
            return 0.0
        
        # 简化版: 基于草案长度和内容差异
        # 实际可用语义相似度计算
        unique_tokens = set()
        for draft in drafts:
            tokens = set(draft.draft.split())
            unique_tokens.update(tokens)
        
        total_tokens = sum(len(d.draft.split()) for d in drafts)
        if total_tokens == 0:
            return 0.0
        
        diversity = len(unique_tokens) / total_tokens
        return min(diversity, 1.0)
    
    async def _aggregate(
        self,
        drafts: List[AgentDraft],
        strategy: AggregationStrategy
    ) -> Optional[AgentDraft]:
        """
        阶段2: 聚合选优
        """
        if not drafts:
            return None
        
        if strategy == AggregationStrategy.VOTE:
            # 按置信度投票
            return max(drafts, key=lambda d: d.confidence)
        
        elif strategy == AggregationStrategy.EXPERT:
            # 专家裁决 (选择特定角色)
            for d in drafts:
                if d.agent_role in ["Architect", "SecurityAuditor"]:
                    return d
            return drafts[0]
        
        elif strategy == AggregationStrategy.CONSENSUS:
            # 共识评估 (需要WaldConsensus)
            return max(drafts, key=lambda d: d.confidence)
        
        else:
            # 默认选最高置信度
            return max(drafts, key=lambda d: d.confidence)


# CLI 命令集成
async def parallel_command(task: str, agents: str = "Architect,Coder,SecurityAuditor"):
    """
    /parallel 命令 - 并发执行模式
    
    用法: council parallel "重构认证模块" --agents "Architect,Coder"
    """
    executor = ParallelExecutor()
    agent_list = [a.strip() for a in agents.split(",")]
    
    result = await executor.execute_parallel(task, agent_list)
    
    print(f"📊 并发执行结果")
    print(f"   任务: {result.task}")
    print(f"   草案数: {len(result.drafts)}")
    print(f"   多样性: {result.diversity_score:.2f}")
    print(f"   耗时: {result.execution_time_ms:.0f}ms")
    
    if result.selected_draft:
        print(f"   选优: {result.selected_draft.agent_id} (置信度: {result.selected_draft.confidence})")
    
    return result


__all__ = [
    "ParallelExecutor",
    "ParallelResult",
    "AgentDraft",
    "AggregationStrategy",
    "parallel_command",
]
