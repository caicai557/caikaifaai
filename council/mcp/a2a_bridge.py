"""
A2A Bridge - Agent-to-Agent Protocol Bridge

Bridges between internal Council agents and external MCP servers.
Based on 2025 Anthropic MCP + Google A2A patterns.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime
from enum import Enum
import logging
import json

logger = logging.getLogger(__name__)


class AgentCapability(Enum):
    """Standard agent capabilities"""

    THINK = "think"
    VOTE = "vote"
    EXECUTE = "execute"
    CODE = "code"
    REVIEW = "review"
    SECURITY_AUDIT = "security_audit"
    ARCHITECTURE = "architecture"
    SEARCH = "search"
    HANDOFF = "handoff"


@dataclass
class AgentCapabilityDescriptor:
    """
    Describes an agent's capabilities for discovery

    Used for dynamic agent discovery in A2A protocol.
    """

    agent_name: str
    capabilities: List[AgentCapability]
    description: str
    input_schema: Dict[str, Any] = field(default_factory=dict)
    output_schema: Dict[str, Any] = field(default_factory=dict)
    version: str = "1.0.0"
    priority: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to JSON-compatible dict"""
        return {
            "name": self.agent_name,
            "capabilities": [c.value for c in self.capabilities],
            "description": self.description,
            "input_schema": self.input_schema,
            "output_schema": self.output_schema,
            "version": self.version,
            "priority": self.priority,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AgentCapabilityDescriptor":
        """Create from dict"""
        return cls(
            agent_name=data["name"],
            capabilities=[AgentCapability(c) for c in data.get("capabilities", [])],
            description=data.get("description", ""),
            input_schema=data.get("input_schema", {}),
            output_schema=data.get("output_schema", {}),
            version=data.get("version", "1.0.0"),
            priority=data.get("priority", 0),
        )


@dataclass
class A2AMessage:
    """
    A2A Protocol message

    Represents a message between agents or MCP servers.
    """

    message_id: str
    from_agent: str
    to_agent: str
    action: str
    payload: Dict[str, Any]
    timestamp: datetime = field(default_factory=datetime.now)
    reply_to: Optional[str] = None
    correlation_id: Optional[str] = None

    def to_json(self) -> str:
        """Serialize to JSON"""
        return json.dumps(
            {
                "message_id": self.message_id,
                "from_agent": self.from_agent,
                "to_agent": self.to_agent,
                "action": self.action,
                "payload": self.payload,
                "timestamp": self.timestamp.isoformat(),
                "reply_to": self.reply_to,
                "correlation_id": self.correlation_id,
            }
        )


# Type for message handlers
MessageHandler = Callable[[A2AMessage], Optional[A2AMessage]]


class A2ABridge:
    """
    Bridge between Council agents and external MCP servers

    Features:
    - Agent capability discovery
    - Message routing (MCP -> Council, Council -> MCP)
    - Protocol translation
    """

    def __init__(self):
        self._agents: Dict[str, AgentCapabilityDescriptor] = {}
        self._handlers: Dict[str, MessageHandler] = {}
        self._pending_messages: List[A2AMessage] = []
        self._message_log: List[A2AMessage] = []

    def register_agent(self, descriptor: AgentCapabilityDescriptor) -> None:
        """
        Register an agent's capabilities

        Args:
            descriptor: Agent capability descriptor
        """
        self._agents[descriptor.agent_name] = descriptor
        logger.info(
            f"Registered agent: {descriptor.agent_name} "
            f"with capabilities: {[c.value for c in descriptor.capabilities]}"
        )

    def register_handler(self, agent_name: str, handler: MessageHandler) -> None:
        """
        Register a message handler for an agent

        Args:
            agent_name: Agent name
            handler: Message handler function
        """
        self._handlers[agent_name] = handler

    def discover_agents(
        self, capability: Optional[AgentCapability] = None
    ) -> List[AgentCapabilityDescriptor]:
        """
        Discover available agents

        Args:
            capability: Optional capability filter

        Returns:
            List of matching agent descriptors
        """
        if capability is None:
            return list(self._agents.values())

        return [
            desc for desc in self._agents.values() if capability in desc.capabilities
        ]

    def route_to_best_agent(
        self, capability: AgentCapability, message: A2AMessage
    ) -> Optional[A2AMessage]:
        """
        Route message to the best agent for a capability

        Args:
            capability: Required capability
            message: Message to route

        Returns:
            Response message or None
        """
        candidates = self.discover_agents(capability)
        if not candidates:
            logger.warning(f"No agents found with capability: {capability.value}")
            return None

        # Sort by priority (highest first)
        candidates.sort(key=lambda d: d.priority, reverse=True)
        best_agent = candidates[0]

        # Update message destination
        message.to_agent = best_agent.agent_name

        return self.send_message(message)

    def send_message(self, message: A2AMessage) -> Optional[A2AMessage]:
        """
        Send a message to an agent

        Args:
            message: Message to send

        Returns:
            Response message or None
        """
        self._message_log.append(message)
        logger.info(
            f"A2A: {message.from_agent} -> {message.to_agent} ({message.action})"
        )

        # Find handler
        handler = self._handlers.get(message.to_agent)
        if handler:
            try:
                response = handler(message)
                if response:
                    self._message_log.append(response)
                return response
            except Exception as e:
                logger.error(f"Handler error for {message.to_agent}: {e}")
                return None
        else:
            # Queue for later processing
            self._pending_messages.append(message)
            logger.debug(f"Message queued for: {message.to_agent}")
            return None

    def process_pending(self) -> int:
        """
        Process pending messages

        Returns:
            Number of messages processed
        """
        processed = 0
        remaining = []

        for message in self._pending_messages:
            handler = self._handlers.get(message.to_agent)
            if handler:
                try:
                    handler(message)
                    processed += 1
                except Exception as e:
                    logger.error(f"Failed to process message: {e}")
                    remaining.append(message)
            else:
                remaining.append(message)

        self._pending_messages = remaining
        return processed

    def create_mcp_tool_response(
        self, agent_response: str, agent_name: str
    ) -> Dict[str, Any]:
        """
        Convert agent response to MCP tool response format

        Args:
            agent_response: Agent's response text
            agent_name: Name of the responding agent

        Returns:
            MCP-compatible response dict
        """
        return {
            "content": [
                {
                    "type": "text",
                    "text": agent_response,
                }
            ],
            "metadata": {
                "agent": agent_name,
                "protocol": "a2a",
                "version": "1.0.0",
            },
        }

    def get_message_log(self, limit: int = 50) -> List[Dict]:
        """Get recent message log"""
        return [
            {
                "id": m.message_id,
                "from": m.from_agent,
                "to": m.to_agent,
                "action": m.action,
                "timestamp": m.timestamp.isoformat(),
            }
            for m in self._message_log[-limit:]
        ]


def generate_message_id() -> str:
    """Generate a unique message ID"""
    import uuid

    return f"msg_{uuid.uuid4().hex[:12]}"


# Export
__all__ = [
    "A2ABridge",
    "A2AMessage",
    "AgentCapability",
    "AgentCapabilityDescriptor",
    "MessageHandler",
    "generate_message_id",
]
