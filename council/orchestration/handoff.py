"""
Agent Handoff - Swarm-style clean agent transfers

Based on OpenAI Swarm patterns: "Clean transfers of control between agents."
Provides structured handoff with context snapshots and explicit boundaries.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class HandoffPriority(Enum):
    """Handoff priority levels"""

    LOW = 0
    NORMAL = 1
    HIGH = 2
    CRITICAL = 3


class HandoffStatus(Enum):
    """Handoff status"""

    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class ContextSnapshot:
    """
    Bounded context snapshot for handoff

    Contains only the essential information needed for the target agent.
    Prevents token overflow by limiting context size.
    """

    task_summary: str
    recent_decisions: List[str] = field(default_factory=list)
    key_facts: Dict[str, Any] = field(default_factory=dict)
    constraints: List[str] = field(default_factory=list)
    max_items: int = 10  # Bounded context

    def add_decision(self, decision: str) -> None:
        """Add a decision, keeping only the most recent max_items"""
        self.recent_decisions.append(decision)
        if len(self.recent_decisions) > self.max_items:
            self.recent_decisions = self.recent_decisions[-self.max_items :]

    def add_fact(self, key: str, value: Any) -> None:
        """Add a key fact"""
        self.key_facts[key] = value

    def to_prompt(self) -> str:
        """Convert to a prompt-friendly string"""
        lines = [f"## Task: {self.task_summary}"]

        if self.recent_decisions:
            lines.append("\n### Recent Decisions:")
            for d in self.recent_decisions[-5:]:  # Only last 5
                lines.append(f"- {d}")

        if self.key_facts:
            lines.append("\n### Key Facts:")
            for k, v in list(self.key_facts.items())[:5]:  # Only first 5
                lines.append(f"- {k}: {v}")

        if self.constraints:
            lines.append("\n### Constraints:")
            for c in self.constraints[:3]:  # Only first 3
                lines.append(f"- {c}")

        return "\n".join(lines)


@dataclass
class AgentHandoff:
    """
    Represents a clean handoff between agents

    This is the core data structure for Swarm-style agent transfers.
    """

    from_agent: str
    to_agent: str
    context: ContextSnapshot
    reason: str
    priority: HandoffPriority = HandoffPriority.NORMAL
    status: HandoffStatus = HandoffStatus.PENDING
    created_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    result: Optional[str] = None
    error: Optional[str] = None

    def accept(self) -> None:
        """Mark handoff as accepted"""
        self.status = HandoffStatus.ACCEPTED

    def complete(self, result: str) -> None:
        """Mark handoff as completed"""
        self.status = HandoffStatus.COMPLETED
        self.result = result
        self.completed_at = datetime.now()

    def fail(self, error: str) -> None:
        """Mark handoff as failed"""
        self.status = HandoffStatus.FAILED
        self.error = error
        self.completed_at = datetime.now()

    def reject(self, reason: str) -> None:
        """Mark handoff as rejected"""
        self.status = HandoffStatus.REJECTED
        self.error = reason
        self.completed_at = datetime.now()


# Type for handoff callbacks
HandoffCallback = Callable[[AgentHandoff], None]


class HandoffManager:
    """
    Manages agent handoffs with Pub/Sub integration

    Features:
    - Clean context transfer between agents
    - Priority-based handoff queue
    - Event-driven notifications via Hub
    """

    def __init__(self, hub: Optional["Hub"] = None):
        """
        Initialize the handoff manager

        Args:
            hub: Optional Hub for Pub/Sub integration
        """
        self.hub = hub
        self._pending: List[AgentHandoff] = []
        self._history: List[AgentHandoff] = []
        self._callbacks: Dict[str, List[HandoffCallback]] = {}

    def initiate_handoff(
        self,
        from_agent: str,
        to_agent: str,
        task_summary: str,
        reason: str,
        priority: HandoffPriority = HandoffPriority.NORMAL,
        context: Optional[ContextSnapshot] = None,
    ) -> AgentHandoff:
        """
        Initiate a handoff to another agent

        Args:
            from_agent: Source agent name
            to_agent: Target agent name
            task_summary: Brief summary of the task
            reason: Why the handoff is happening
            priority: Handoff priority
            context: Optional pre-built context snapshot

        Returns:
            AgentHandoff object
        """
        if context is None:
            context = ContextSnapshot(task_summary=task_summary)

        handoff = AgentHandoff(
            from_agent=from_agent,
            to_agent=to_agent,
            context=context,
            reason=reason,
            priority=priority,
        )

        self._pending.append(handoff)
        self._pending.sort(key=lambda h: h.priority.value, reverse=True)

        logger.info(f"Handoff initiated: {from_agent} -> {to_agent} ({reason})")

        # Notify via Hub if available
        if self.hub:
            from council.orchestration.events import Event, EventType

            self.hub.publish(
                Event(
                    type=EventType.HANDOFF_INITIATED,
                    source=from_agent,
                    payload={
                        "to_agent": to_agent,
                        "reason": reason,
                        "priority": priority.value,
                    },
                )
            )

        # Notify callbacks
        if to_agent in self._callbacks:
            for callback in self._callbacks[to_agent]:
                try:
                    callback(handoff)
                except Exception as e:
                    logger.error(f"Handoff callback error: {e}")

        return handoff

    def accept_handoff(self, handoff: AgentHandoff) -> None:
        """Accept a pending handoff"""
        if handoff in self._pending:
            handoff.accept()
            logger.info(f"Handoff accepted by {handoff.to_agent}")

    def complete_handoff(self, handoff: AgentHandoff, result: str) -> None:
        """Complete a handoff with result"""
        handoff.complete(result)
        if handoff in self._pending:
            self._pending.remove(handoff)
        self._history.append(handoff)

        logger.info(f"Handoff completed: {handoff.from_agent} -> {handoff.to_agent}")

        # Notify via Hub
        if self.hub:
            from council.orchestration.events import Event, EventType

            self.hub.publish(
                Event(
                    type=EventType.HANDOFF_COMPLETED,
                    source=handoff.to_agent,
                    payload={
                        "from_agent": handoff.from_agent,
                        "result": result[:200],  # Truncate for event
                    },
                )
            )

    def register_callback(self, agent_name: str, callback: HandoffCallback) -> None:
        """Register a callback for when an agent receives a handoff"""
        if agent_name not in self._callbacks:
            self._callbacks[agent_name] = []
        self._callbacks[agent_name].append(callback)

    def get_pending_for_agent(self, agent_name: str) -> List[AgentHandoff]:
        """Get all pending handoffs for an agent"""
        return [h for h in self._pending if h.to_agent == agent_name]

    def get_history(self, limit: int = 20) -> List[AgentHandoff]:
        """Get handoff history"""
        return self._history[-limit:]


# Export
__all__ = [
    "AgentHandoff",
    "ContextSnapshot",
    "HandoffManager",
    "HandoffPriority",
    "HandoffStatus",
    "HandoffCallback",
]
