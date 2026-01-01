"""
PM Phase - 需求代码化阶段

使用 Codex 模型将模糊需求转化为结构化任务树和 PRD 文档。
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime

from council.agents.base_agent import ModelConfig


@dataclass
class TaskNode:
    """任务树节点"""
    id: str
    title: str
    description: str
    priority: str = "P1"  # P0, P1, P2
    assigned_agent: str = "Coder"
    children: List["TaskNode"] = field(default_factory=list)
    status: str = "pending"


@dataclass
class PRDocument:
    """需求文档"""
    title: str
    background: str
    goals: List[str]
    non_goals: List[str]
    task_tree: List[TaskNode]
    created_at: datetime = field(default_factory=datetime.now)


class RequirementParser:
    """
    需求解析器 - 使用 Codex 模型
    
    将用户的模糊需求解析为结构化数据
    """
    model = ModelConfig.CODEX
    
    def __init__(self, llm_client: Optional[Any] = None):
        self.llm_client = llm_client
    
    def parse(self, user_input: str) -> Dict[str, Any]:
        """
        解析用户输入
        
        Args:
            user_input: 用户的需求描述
            
        Returns:
            结构化需求数据
        """
        # TODO: 调用 LLM 进行解析
        return {
            "title": user_input[:50],
            "goals": [],
            "non_goals": [],
            "complexity": "medium",
        }


class TaskTreeGenerator:
    """
    任务树生成器
    
    将需求拆解为可执行的任务树
    """
    model = ModelConfig.CODEX
    
    def __init__(self, llm_client: Optional[Any] = None):
        self.llm_client = llm_client
    
    def generate(self, requirement: Dict[str, Any]) -> List[TaskNode]:
        """
        生成任务树
        
        Args:
            requirement: 结构化需求数据
            
        Returns:
            任务节点列表
        """
        # TODO: 调用 LLM 生成任务树
        return [
            TaskNode(
                id="TASK-001",
                title=requirement.get("title", "Unknown"),
                description="待分解",
            )
        ]


class PRDGenerator:
    """
    PRD 文档生成器
    """
    model = ModelConfig.CODEX
    
    def generate(
        self,
        requirement: Dict[str, Any],
        task_tree: List[TaskNode]
    ) -> PRDocument:
        """生成 PRD 文档"""
        return PRDocument(
            title=requirement.get("title", "Untitled"),
            background="",
            goals=requirement.get("goals", []),
            non_goals=requirement.get("non_goals", []),
            task_tree=task_tree,
        )


__all__ = ["RequirementParser", "TaskTreeGenerator", "PRDGenerator", "TaskNode", "PRDocument"]
