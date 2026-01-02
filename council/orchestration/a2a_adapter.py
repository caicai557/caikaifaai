"""
A2A Protocol Adapter - Agent-to-Agent Communication (2026 Best Practice)

Implements Google A2A / IBM ACP compatible patterns for:
- Agent Discovery (AgentCard)
- Task Negotiation (TaskContract)
- Capability Advertisement
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from enum import Enum
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class AgentCapability(Enum):
    """Agent capability categories (A2A standard)"""

    CODE_GENERATION = "code_generation"
    CODE_REVIEW = "code_review"
    SECURITY_AUDIT = "security_audit"
    WEB_RESEARCH = "web_research"
    ARCHITECTURE = "architecture"
    TESTING = "testing"
    DOCUMENTATION = "documentation"
    ORCHESTRATION = "orchestration"


@dataclass
class AgentCard:
    """
    Agent Card - A2A Protocol Agent Advertisement

    An Agent Card describes an agent's:
    - Identity (name, version)
    - Capabilities (what it can do)
    - Constraints (token limits, rate limits)
    - Endpoint (how to reach it)

    This is analogous to an "API specification" but for agents.
    """

    name: str
    description: str
    version: str = "1.0.0"
    capabilities: List[AgentCapability] = field(default_factory=list)
    keywords: List[str] = field(default_factory=list)
    max_context_tokens: int = 128000  # Context window limit
    rate_limit_rpm: int = 60  # Requests per minute
    preferred_task_types: List[str] = field(default_factory=list)
    supported_protocols: List[str] = field(default_factory=lambda: ["mcp", "a2a"])
    metadata: Dict[str, Any] = field(default_factory=dict)

    def matches_query(self, query: str) -> float:
        """Calculate match score (0-1) for a query"""
        query_lower = query.lower()
        score = 0.0

        # Name match
        if self.name.lower() in query_lower:
            score += 0.5

        # Keyword match
        for kw in self.keywords:
            if kw.lower() in query_lower:
                score += 0.2

        # Capability match
        for cap in self.capabilities:
            if cap.value.replace("_", " ") in query_lower:
                score += 0.3

        return min(1.0, score)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary (for network transport)"""
        return {
            "name": self.name,
            "description": self.description,
            "version": self.version,
            "capabilities": [c.value for c in self.capabilities],
            "keywords": self.keywords,
            "max_context_tokens": self.max_context_tokens,
            "rate_limit_rpm": self.rate_limit_rpm,
            "preferred_task_types": self.preferred_task_types,
            "supported_protocols": self.supported_protocols,
            "metadata": self.metadata,
        }


class TaskStatus(Enum):
    """Task lifecycle status"""

    PROPOSED = "proposed"
    NEGOTIATING = "negotiating"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class TaskContract:
    """
    Task Contract - A2A Protocol Task Agreement

    Represents a negotiated agreement between agents for task execution.
    """

    task_id: str
    from_agent: str
    to_agent: str
    description: str
    expected_output: str
    priority: int = 1  # 1 (low) - 5 (critical)
    deadline_seconds: Optional[int] = None
    context: Dict[str, Any] = field(default_factory=dict)
    status: TaskStatus = TaskStatus.PROPOSED
    created_at: datetime = field(default_factory=datetime.now)
    accepted_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result: Optional[str] = None

    def accept(self) -> None:
        """Mark contract as accepted"""
        self.status = TaskStatus.ACCEPTED
        self.accepted_at = datetime.now()

    def reject(self, reason: str) -> None:
        """Mark contract as rejected"""
        self.status = TaskStatus.REJECTED
        self.context["rejection_reason"] = reason

    def complete(self, result: str) -> None:
        """Mark contract as completed"""
        self.status = TaskStatus.COMPLETED
        self.result = result
        self.completed_at = datetime.now()

    def fail(self, error: str) -> None:
        """Mark contract as failed"""
        self.status = TaskStatus.FAILED
        self.context["error"] = error
        self.completed_at = datetime.now()


class AgentDiscovery:
    """
    Agent Discovery Service - A2A Protocol

    Maintains a registry of available agents and their capabilities.
    Supports querying agents by capability, task type, or natural language.
    """

    def __init__(self):
        self._agents: Dict[str, AgentCard] = {}

    def register(self, card: AgentCard) -> None:
        """Register an agent"""
        self._agents[card.name] = card
        logger.info(
            f"A2A: Registered agent {card.name} with capabilities: {[c.value for c in card.capabilities]}"
        )

    def unregister(self, name: str) -> bool:
        """Unregister an agent"""
        if name in self._agents:
            del self._agents[name]
            logger.info(f"A2A: Unregistered agent {name}")
            return True
        return False

    def discover(
        self,
        query: Optional[str] = None,
        capability: Optional[AgentCapability] = None,
        top_k: int = 5,
    ) -> List[AgentCard]:
        """
        Discover agents matching criteria

        Args:
            query: Natural language query
            capability: Required capability
            top_k: Maximum results

        Returns:
            List of matching AgentCards
        """
        candidates = []

        for card in self._agents.values():
            # Capability filter
            if capability and capability not in card.capabilities:
                continue

            # Query scoring
            if query:
                score = card.matches_query(query)
                if score > 0.1:
                    candidates.append((score, card))
            else:
                candidates.append((1.0, card))

        # Sort by score
        candidates.sort(key=lambda x: x[0], reverse=True)

        return [card for _, card in candidates[:top_k]]

    def get(self, name: str) -> Optional[AgentCard]:
        """Get agent by name"""
        return self._agents.get(name)

    def list_all(self) -> List[AgentCard]:
        """List all registered agents"""
        return list(self._agents.values())

    def get_stats(self) -> Dict[str, Any]:
        """Get discovery service stats"""
        capability_counts = {}
        for card in self._agents.values():
            for cap in card.capabilities:
                capability_counts[cap.value] = capability_counts.get(cap.value, 0) + 1

        return {
            "total_agents": len(self._agents),
            "capability_distribution": capability_counts,
        }


# Global discovery instance
_default_discovery: Optional[AgentDiscovery] = None


def get_discovery() -> AgentDiscovery:
    """Get global discovery service"""
    global _default_discovery
    if _default_discovery is None:
        _default_discovery = AgentDiscovery()
    return _default_discovery


__all__ = [
    "AgentCard",
    "AgentCapability",
    "AgentDiscovery",
    "TaskContract",
    "TaskStatus",
    "get_discovery",
]
