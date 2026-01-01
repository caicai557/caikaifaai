# Council Module - 智能体理事会核心模块

# Core agents
from council.agents import BaseAgent, Architect, Coder, SecurityAuditor
from council.facilitator import Facilitator, WaldConsensus
from council.auth import RBAC

# Orchestration
from council.orchestration import (
    AgentRegistry,
    DelegationManager,
    TaskClassifier,
    ModelRouter,
    ModelConfig,
    RoutingResult,
    HandoffManager,
    ContextSnapshot,
    AgentHandoff,
)

# Persistence
from council.persistence.checkpoint import Checkpoint
from council.persistence.state_store import SqliteStateStore
from council.persistence.redis_store import RedisStateStore, RedisDistributedLock

# Observability
from council.observability import AgentTracer
from council.observability.middleware import LocalMemory, observable

# Memory
from council.memory.vector_memory import VectorMemory
from council.memory.rag_retriever import RAGRetriever

# Streaming
from council.streaming import StreamingLLM, SSEFormatter
from council.sandbox import (
    SandboxProvider,
    SandboxResult,
    SandboxRunner,
    LocalSandboxRunner,
    DockerSandboxRunner,
    E2BSandboxRunner,
    get_sandbox_runner,
)

# Tools (1.0.0)
from council.tools import (
    ProgrammaticToolExecutor,
    ToolExecutionError,
    SandboxViolationError,
)

# Core Orchestrator (1.0.0)
from council.dev_orchestrator import DevOrchestrator, DevResult, DevStatus

__version__ = "1.0.0"

__all__ = [
    # Core
    "BaseAgent",
    "Architect",
    "Coder",
    "SecurityAuditor",
    "Facilitator",
    "WaldConsensus",
    "RBAC",
    # Orchestration
    "AgentRegistry",
    "DelegationManager",
    "TaskClassifier",
    "ModelRouter",
    "ModelConfig",
    "RoutingResult",
    "HandoffManager",
    "ContextSnapshot",
    "AgentHandoff",
    "DevOrchestrator",
    "DevResult",
    "DevStatus",
    # Persistence
    "Checkpoint",
    "SqliteStateStore",
    "RedisStateStore",
    "RedisDistributedLock",
    # Observability
    "AgentTracer",
    "LocalMemory",
    "observable",
    # Memory
    "VectorMemory",
    "RAGRetriever",
    # Streaming
    "StreamingLLM",
    "SSEFormatter",
    # Tools (1.0.0)
    "ProgrammaticToolExecutor",
    "ToolExecutionError",
    "SandboxViolationError",
    # Sandbox
    "SandboxProvider",
    "SandboxResult",
    "SandboxRunner",
    "LocalSandboxRunner",
    "DockerSandboxRunner",
    "E2BSandboxRunner",
    "get_sandbox_runner",
]
