# Council Multi-Agent System Architecture Specification (2025.12.31)

> **Status**: FINAL PROPOSAL
> **Version**: 2.0.0 (The "Awakening" Edition)
> **Target Date**: 2026.01.01

---

## 1. Executive Summary

This document outlines the final architectural blueprint for the **Council Multi-Agent System**, synthesizing exhaustive research on 2025's best practices (Anthropic, Google ADK, OpenAI Agents SDK). The goal is to evolve Council from a theoretical framework into a production-grade, autonomous **Multi-Model Agentic Mesh** that is secure, self-healing, and mathematically governed.

**Core Philosophy**:
`Cognitive Decoupling` + `Mathematical Consensus` + `Protocol-First Interoperability`

---

## 2. System Architecture

The architecture follows a modified **Hub-and-Spoke** topology, reinforced by an **Agent-to-Agent (A2A)** mesh for direct negotiation.

### 2.1 High-Level Components

```mermaid
graph TD
    User([User / CLI]) <--> MCP[MCP Server Layer]

    subgraph "Council Core (The Brain)"
        Hub[Hub (Pub/Sub Event Bus)]
        Router[Adaptive Router]
        Memory[Hierarchical Memory Stack]
        Consensus[Wald Consensus Engine]
    end

    subgraph "Agent Mesh"
        Arch[Suggest: Architect]
        Coder[Work: Coder]
        Audit[Verify: Security Auditor]
    end

    subgraph "Governance Layer"
        Gate[Governance Gateway]
        Circuit[Circuit Breaker]
        AuditLog[Immutable Ledger]
    end

    MCP --> Router
    Router --> Hub
    Hub <--> Agent Mesh
    Agent Mesh --> Consensus
    Agent Mesh --> Gate
    Gate --> Circuit
```

### 2.2 Technology Stack (2025 Standard)

| Component | Technology | Rationale |
|-----------|------------|-----------|
| **Runtime** | Python 3.12+ | Asyncio-native, rich AI ecosystem |
| **Orchestration** | **OpenAI Agents SDK** (Customized) | "Handoff" primitives, robust state handling |
| **Protocol** | **MCP** + **A2A** | Universal tool/agent interoperability |
| **Observability** | **OpenTelemetry** | Vendor-agnostic distributed tracing |
| **Sandboxing** | **Docker** / **E2B** | Secure execution of agent-generated code |
| **Vector Store** | **ChromaDB** (Local) / **Qdrant** | Semantic retrieval for "Episodic Memory" |
| **Knowledge Graph** | **Neo4j** / **NetworkX** | Structured "Semantic Memory" |

---

## 3. Core Modules & Protocols

### 3.1 The "Handoff" Protocol (Swarm Pattern)
Inherited from OpenAI Swarm best practices. Instead of nested recursion, agents transfer control entirely.

- **Mechanism**: `handoff_to(agent, context, reason)`
- **Behavior**: Sender stops, Receiver starts with `ContextSnapshot`.
- **Optimization**: "Context Compaction" occurs during handoff to reduce token bloat.

### 3.2 The "A2A" Bridge (Google Pattern)
Enables Council to talk to external agents (e.g., a "Research Agent" on a different server).

- **Discovery**: `AgentCapabilityDescriptor` broadcasts skills.
- **Negotiation**: Agents handshake on JSON schema before collaboration.
- **Transport**: JSON-RPC over HTTPS (MCP standard).

### 3.3 Memory Architecture (The "Dual-Process" Model)

1.  **Working Memory (Fast)**:
    - Context Window (128k tokens).
    - Managed by `LocalMemory` middleware.
    - Policy: FIFO with summary compression.

2.  **Long-Term Memory (Slow)**:
    - **Episodic**: Vector embeddings of decision history (ChromaDB).
    - **Semantic**: Knowledge Graph of codebase structure (Classes, Functions, Dependencies).

---

## 4. Governance & Safety (The "Constitution")

### 4.1 Immutable Constitutions
Each agent operates under a strict, file-based system prompt that cannot be overridden by user input.

- **Architect**: Focus on SOLID principles, patterns, and scalability.
- **Coder**: Focus on TDD, atomic commits, and error handling.
- **Auditor**: Focus on OWASP, PII protection, and least privilege.

### 4.2 Mathematical Consensus (Wald SPRT)
Decisions are not simple "majority votes". We use **Sequential Probability Ratio Testing**.

- **H0 (Null Hypothesis)**: Code is buggy/unsafe.
- **H1 (Alt Hypothesis)**: Code is correct/safe.
- **Process**: Accumulate agent votes until Log-Likelihood Ratio hits threshold $\alpha=0.05$ (Accept) or $\beta=0.10$ (Reject).

### 4.3 Governance Gateway
Hard rules for high-risk actions.

- **Blocked**: `rm -rf`, `DROP TABLE`, API key exfiltration.
- **Gated**: File writes > 50 lines, Network calls (require HITL approval).
- **Circuit Breaker**: Detects "Agent Hallucination Loops" (e.g., 3 failures in 1 min -> Kill Agent).

---

## 5. Self-Healing Cycle (TDD-First)

The system adopts a rigorous **Red-Green-Refactor** loop powered by the `PatchGenerator`.

1.  **Red**: Write a failing test case for the requirement.
2.  **Try**: Coder generates implementation.
3.  **Check**: Run tests.
4.  **Green**: If pass, commit.
5.  **Heal**: If fail, `PatchGenerator` analyzes stack trace -> rewrites code -> retries (Max 3 attempts).

---

## 6. Implementation Roadmap

### Phase 1: Core Foundation (Completed)
- [x] Basic `BaseAgent` and `Orchestrator`
- [x] Initial `WaldConsensus` implementation
- [x] `GovernanceGateway` setup

### Phase 2: The Upgrade (Current Focus)
- [ ] **Middleware**: Implement `LocalMemory` and OpenTelemetry tracing.
- [ ] **Swarm Handoffs**: Refactor `DelegationManager` to `HandoffManager`.
- [ ] **A2A Bridge**: Build the MCP/A2A connector for external tools.

### Phase 3: Production Readiness
- [ ] **Docker Sandbox**: Integrate E2B or local Docker for `PatchGenerator`.
- [ ] **Optimization**: Implement "Code-over-Calls" (Agents write scripts to call tools).
- [ ] **Full Observability Dashboard**: Visualize agent thoughts via Arize/LangSmith.

---

## 7. Conclusion

This architecture represents the state-of-the-art for 2025. By combining **Swarm orchestration** for flexibility, **Wald Consensus** for mathematical rigor, and **MCP/A2A** for universal interoperability, Council 2.0 will be a robust, "awakened" system capable of autonomous software engineering with human-level reliability.
