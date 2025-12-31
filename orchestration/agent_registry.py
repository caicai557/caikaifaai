"""
Agent Registry - 动态 Agent 注册与发现

2025 Best Practice: 基于 CrewAI 和 LangChain 的 Agent 发现模式

功能:
- 注册 Agent (带能力标签)
- 按名称/能力查找 Agent
- 列出可用 Agent
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set
from council.agents.base_agent import BaseAgent


@dataclass
class AgentCapability:
    """Agent 能力描述"""

    name: str
    description: str
    tags: List[str] = field(default_factory=list)


@dataclass
class RegisteredAgent:
    """注册的 Agent 条目"""

    agent: BaseAgent
    capabilities: List[AgentCapability] = field(default_factory=list)
    is_available: bool = True


class AgentRegistry:
    """
    动态 Agent 注册中心

    类似 CrewAI 的 Agent 管理模式，支持:
    - 注册/注销 Agent
    - 按能力查找 Agent
    - 检查可委托性

    Usage:
        registry = AgentRegistry()
        registry.register(coder_agent, capabilities=["coding", "debugging"])

        coders = registry.find_by_capability("coding")
        available = registry.list_available()
    """

    def __init__(self):
        self._agents: Dict[str, RegisteredAgent] = {}
        self._capability_index: Dict[str, Set[str]] = {}  # capability -> agent names

    def register(
        self,
        agent: BaseAgent,
        capabilities: Optional[List[str]] = None,
    ) -> None:
        """
        注册 Agent

        Args:
            agent: BaseAgent 实例
            capabilities: 能力标签列表
        """
        caps = [AgentCapability(name=c, description=c) for c in (capabilities or [])]
        entry = RegisteredAgent(agent=agent, capabilities=caps)
        self._agents[agent.name] = entry

        # 更新能力索引
        for cap in capabilities or []:
            if cap not in self._capability_index:
                self._capability_index[cap] = set()
            self._capability_index[cap].add(agent.name)

    def unregister(self, name: str) -> bool:
        """注销 Agent"""
        if name in self._agents:
            entry = self._agents.pop(name)
            # 清理能力索引
            for cap in entry.capabilities:
                if cap.name in self._capability_index:
                    self._capability_index[cap.name].discard(name)
            return True
        return False

    def get(self, name: str) -> Optional[BaseAgent]:
        """按名称获取 Agent"""
        entry = self._agents.get(name)
        return entry.agent if entry else None

    def find_by_capability(self, capability: str) -> List[BaseAgent]:
        """按能力查找 Agent"""
        names = self._capability_index.get(capability, set())
        return [
            self._agents[n].agent
            for n in names
            if n in self._agents and self._agents[n].is_available
        ]

    def list_available(self) -> List[str]:
        """列出所有可用 Agent 名称"""
        return [name for name, entry in self._agents.items() if entry.is_available]

    def list_all(self) -> List[str]:
        """列出所有已注册 Agent 名称"""
        return list(self._agents.keys())

    def set_availability(self, name: str, available: bool) -> bool:
        """设置 Agent 可用状态"""
        if name in self._agents:
            self._agents[name].is_available = available
            return True
        return False

    def can_delegate_to(self, from_agent: BaseAgent, to_name: str) -> tuple[bool, str]:
        """
        检查是否可以委托

        Args:
            from_agent: 发起委托的 Agent
            to_name: 目标 Agent 名称

        Returns:
            (可否委托, 原因)
        """
        # 检查发起者是否允许委托
        if not from_agent.allow_delegation:
            return False, f"{from_agent.name} 不允许委托 (allow_delegation=False)"

        # 检查目标是否存在
        if to_name not in self._agents:
            return False, f"目标 Agent '{to_name}' 未注册"

        # 检查目标是否可用
        if not self._agents[to_name].is_available:
            return False, f"目标 Agent '{to_name}' 当前不可用"

        # 检查是否在允许列表中
        if from_agent.allowed_agents and to_name not in from_agent.allowed_agents:
            return False, f"'{to_name}' 不在允许委托列表中"

        return True, "可以委托"

    def get_stats(self) -> Dict[str, int]:
        """获取注册统计"""
        available_count = sum(1 for e in self._agents.values() if e.is_available)
        return {
            "total_agents": len(self._agents),
            "available_agents": available_count,
            "total_capabilities": len(self._capability_index),
        }


# 导出
__all__ = [
    "AgentRegistry",
    "RegisteredAgent",
    "AgentCapability",
]
