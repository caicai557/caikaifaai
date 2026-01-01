"""
Agent Conversation Protocol (2026)

Provides structured communication between agents:
- Message types and routing
- Direct messaging and broadcasting
- Conversation threading
- Message acknowledgment
"""

from __future__ import annotations

import asyncio
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set
import logging

logger = logging.getLogger(__name__)


class MessageType(Enum):
    """Types of messages in agent communication."""

    # Control messages
    REQUEST = "request"
    RESPONSE = "response"
    ACK = "ack"
    NACK = "nack"

    # Content messages
    TASK = "task"
    RESULT = "result"
    FEEDBACK = "feedback"
    QUESTION = "question"
    ANSWER = "answer"

    # Collaboration messages
    PROPOSAL = "proposal"
    VOTE = "vote"
    CONSENSUS = "consensus"
    DELEGATE = "delegate"

    # System messages
    HEARTBEAT = "heartbeat"
    STATUS = "status"
    ERROR = "error"


class Priority(Enum):
    """Message priority levels."""
    LOW = 0
    NORMAL = 1
    HIGH = 2
    URGENT = 3


@dataclass
class Message:
    """
    A message between agents (2026).

    Attributes:
        id: Unique message identifier
        sender: Sender agent name
        receiver: Receiver agent name (or None for broadcast)
        content: Message content
        msg_type: Type of message
        priority: Message priority
        reply_to: ID of message this is replying to
        thread_id: Conversation thread ID
        timestamp: When message was created
        metadata: Additional metadata
        acknowledged: Whether message was acknowledged
    """
    sender: str
    receiver: Optional[str]
    content: Any
    msg_type: MessageType = MessageType.REQUEST
    priority: Priority = Priority.NORMAL
    id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    reply_to: Optional[str] = None
    thread_id: Optional[str] = None
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    metadata: Dict[str, Any] = field(default_factory=dict)
    acknowledged: bool = False

    def is_broadcast(self) -> bool:
        """Check if message is a broadcast."""
        return self.receiver is None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "sender": self.sender,
            "receiver": self.receiver,
            "content": self.content,
            "msg_type": self.msg_type.value,
            "priority": self.priority.value,
            "reply_to": self.reply_to,
            "thread_id": self.thread_id,
            "timestamp": self.timestamp,
            "metadata": self.metadata,
            "acknowledged": self.acknowledged,
        }

    def create_reply(
        self,
        sender: str,
        content: Any,
        msg_type: MessageType = MessageType.RESPONSE,
    ) -> "Message":
        """Create a reply to this message."""
        return Message(
            sender=sender,
            receiver=self.sender,
            content=content,
            msg_type=msg_type,
            reply_to=self.id,
            thread_id=self.thread_id or self.id,
            priority=self.priority,
        )


@dataclass
class ConversationThread:
    """
    A conversation thread between agents.

    Tracks message history and participants.
    """
    id: str
    topic: str
    participants: Set[str] = field(default_factory=set)
    messages: List[Message] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    closed: bool = False

    def add_message(self, message: Message) -> None:
        """Add a message to the thread."""
        self.messages.append(message)
        self.participants.add(message.sender)
        if message.receiver:
            self.participants.add(message.receiver)

    def get_history(self, limit: int = 10) -> List[Message]:
        """Get recent message history."""
        return self.messages[-limit:]


# Type for message handlers
MessageHandler = Callable[[Message], Optional[Message]]
AsyncMessageHandler = Callable[[Message], Any]


class ConversationManager:
    """
    Manager for agent conversations (2026).

    Provides:
    - Message routing
    - Thread management
    - Broadcast messaging
    - Async message handling

    Example:
        manager = ConversationManager()

        # Register agents
        manager.register_agent("planner", handle_planner_message)
        manager.register_agent("coder", handle_coder_message)

        # Send message
        msg = Message(sender="planner", receiver="coder", content="Write tests")
        await manager.send(msg)

        # Broadcast
        await manager.broadcast("planner", "Starting new task", MessageType.STATUS)
    """

    def __init__(self):
        self._agents: Dict[str, AsyncMessageHandler] = {}
        self._queues: Dict[str, asyncio.Queue] = {}
        self._threads: Dict[str, ConversationThread] = {}
        self._message_history: List[Message] = []
        self._pending_acks: Dict[str, asyncio.Event] = {}
        self._lock = asyncio.Lock()

    def register_agent(
        self,
        name: str,
        handler: Optional[AsyncMessageHandler] = None,
    ) -> None:
        """
        Register an agent for messaging.

        Args:
            name: Agent name
            handler: Optional message handler function
        """
        if handler:
            self._agents[name] = handler
        self._queues[name] = asyncio.Queue()
        logger.info(f"Registered agent for messaging: {name}")

    def unregister_agent(self, name: str) -> None:
        """Remove an agent from messaging."""
        self._agents.pop(name, None)
        self._queues.pop(name, None)

    async def send(self, message: Message) -> bool:
        """
        Send a message to an agent.

        Args:
            message: The message to send

        Returns:
            bool: True if message was delivered
        """
        async with self._lock:
            self._message_history.append(message)

        if message.is_broadcast():
            return await self._broadcast_message(message)

        receiver = message.receiver
        if receiver not in self._queues:
            logger.warning(f"Unknown receiver: {receiver}")
            return False

        await self._queues[receiver].put(message)
        logger.debug(f"Message sent: {message.sender} -> {receiver}")

        # Invoke handler if registered
        if receiver in self._agents:
            handler = self._agents[receiver]
            try:
                response = await handler(message)
                if response:
                    await self.send(response)
            except Exception as e:
                logger.error(f"Handler error for {receiver}: {e}")

        return True

    async def _broadcast_message(self, message: Message) -> bool:
        """Broadcast a message to all agents except sender."""
        for agent_name, queue in self._queues.items():
            if agent_name != message.sender:
                await queue.put(message)

        # Invoke all handlers
        for agent_name, handler in self._agents.items():
            if agent_name != message.sender:
                try:
                    await handler(message)
                except Exception as e:
                    logger.error(f"Broadcast handler error for {agent_name}: {e}")

        return True

    async def broadcast(
        self,
        sender: str,
        content: Any,
        msg_type: MessageType = MessageType.STATUS,
        priority: Priority = Priority.NORMAL,
    ) -> Message:
        """
        Broadcast a message to all agents.

        Args:
            sender: Sender agent name
            content: Message content
            msg_type: Message type
            priority: Message priority

        Returns:
            The broadcast message
        """
        message = Message(
            sender=sender,
            receiver=None,
            content=content,
            msg_type=msg_type,
            priority=priority,
        )
        await self.send(message)
        return message

    async def send_and_wait(
        self,
        message: Message,
        timeout: float = 30.0,
    ) -> Optional[Message]:
        """
        Send a message and wait for response.

        Args:
            message: The message to send
            timeout: Maximum wait time in seconds

        Returns:
            Response message or None if timeout
        """
        event = asyncio.Event()
        response_msg: Optional[Message] = None

        async with self._lock:
            self._pending_acks[message.id] = event

        await self.send(message)

        try:
            await asyncio.wait_for(event.wait(), timeout=timeout)
            # Find response in history
            async with self._lock:
                for msg in reversed(self._message_history):
                    if msg.reply_to == message.id:
                        response_msg = msg
                        break
        except asyncio.TimeoutError:
            logger.warning(f"Timeout waiting for response to {message.id}")
        finally:
            self._pending_acks.pop(message.id, None)

        return response_msg

    async def receive(
        self,
        agent_name: str,
        timeout: Optional[float] = None,
    ) -> Optional[Message]:
        """
        Receive a message for an agent.

        Args:
            agent_name: Agent name
            timeout: Optional timeout in seconds

        Returns:
            Message or None if timeout
        """
        if agent_name not in self._queues:
            logger.warning(f"Agent not registered: {agent_name}")
            return None

        queue = self._queues[agent_name]

        try:
            if timeout:
                return await asyncio.wait_for(queue.get(), timeout=timeout)
            else:
                return await queue.get()
        except asyncio.TimeoutError:
            return None

    def create_thread(self, topic: str, initiator: str) -> ConversationThread:
        """
        Create a new conversation thread.

        Args:
            topic: Thread topic
            initiator: Agent starting the thread

        Returns:
            ConversationThread
        """
        thread_id = uuid.uuid4().hex[:8]
        thread = ConversationThread(
            id=thread_id,
            topic=topic,
            participants={initiator},
        )
        self._threads[thread_id] = thread
        return thread

    def get_thread(self, thread_id: str) -> Optional[ConversationThread]:
        """Get a thread by ID."""
        return self._threads.get(thread_id)

    def close_thread(self, thread_id: str) -> None:
        """Close a conversation thread."""
        thread = self._threads.get(thread_id)
        if thread:
            thread.closed = True

    def get_agent_messages(
        self,
        agent_name: str,
        limit: int = 50,
    ) -> List[Message]:
        """Get messages for an agent."""
        return [
            msg for msg in self._message_history[-limit:]
            if msg.sender == agent_name or msg.receiver == agent_name
        ]

    def get_statistics(self) -> Dict[str, Any]:
        """Get messaging statistics."""
        type_counts: Dict[str, int] = {}
        for msg in self._message_history:
            t = msg.msg_type.value
            type_counts[t] = type_counts.get(t, 0) + 1

        return {
            "total_messages": len(self._message_history),
            "active_agents": len(self._agents),
            "active_threads": len([t for t in self._threads.values() if not t.closed]),
            "by_type": type_counts,
        }


# Default conversation manager
default_conversation = ConversationManager()


def send_to(
    sender: str,
    receiver: str,
    content: Any,
    msg_type: MessageType = MessageType.REQUEST,
) -> Message:
    """
    Convenience function to create and queue a message.

    Note: This is synchronous and just creates the message.
    Use await default_conversation.send() to actually send.
    """
    return Message(
        sender=sender,
        receiver=receiver,
        content=content,
        msg_type=msg_type,
    )


__all__ = [
    "Message",
    "MessageType",
    "Priority",
    "ConversationThread",
    "ConversationManager",
    "default_conversation",
    "send_to",
]
