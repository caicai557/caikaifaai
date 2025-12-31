# Council Architecture 2025: Zero-Waste Token Efficiency
> **Date**: 2025.12.28
> **Topic**: High-Performance Multi-Model Agent Governance (Token Optimization Focus)
> **Status**: Research Findings & Gap Analysis

## 1. Executive Summary

By late 2025, the industry expectation for Multi-Agent Systems (MAS) has shifted from "Novelty" to "Production Economics". The cost of "Chatty Agents" (agents assuming a conversational persona) has become the primary bottleneck.

The **2025 Best Practice** for Council Architecture is the **Zero-Waste Protocol**. This paradigm treats agents not as "chatbots in a room" but as "compute nodes in a distributed system".

### Core Philosophy
1.  **Silence is Gold**: If an agent can express intent in 1 token (e.g., a bitmask), it should not use 100 words.
2.  **Lazy Loading**: Context is not "pushed" to agents; it is "pulled" by agents only when referenced.
3.  **Speculative Verification**: Cheap models do 90% of the work; expensive models only resolve distinct conflicts.

---

## 2. Deep Analysis: 2025 Architecture Patterns

### Pattern A: Protocol-First Communication (Agent Protocol Buffers)
**Concept**: Replaces Natural Language (NL) debate with structured schema exchange.
**Token Saving**: ~80% reduction in "Chatter" overhead.

*   **2024 Style (Current in Caicai)**:
    ```text
    Architect: "I have reviewed the proposal. I am concerned about the SQL injection risk in the login module. I suggest we use ORM..."
    ```
*   **2025 Style (Optimized)**:
    ```json
    {
      "role": "Architect",
      "vote": 0, // 0=REJECT, 1=APPROVE
      "risk_vector": ["SECURITY_SQLI"],
      "patch_ref": "3f8a2c"
    }
    ```
    *The "Facilitator" expands this JSON into a summary for humans only if needed, but other agents consume the JSON directly.*

### Pattern B: The "Ledger-Pruning" Strategy (Differential Context)
**Concept**: The Context Window is a cache, not a log.
**Implementation**: Use a **Rolling Summary Window** with "Anchor Points".

*   **Logic**:
    *   **Round 1**: Full Context.
    *   **Round 2**: Full Context + R1.
    *   **Round 3**: `Summary(R1)` + R2.
    *   **Round N**: `Summary(R1...Rn-2)` + Rn-1.
*   **Impact**: Context length becomes $O(1)$ instead of $O(N)$.

### Pattern C: Speculative Consensus (The "Shadow Cabinet")
**Concept**: Use a hierarchy of models to pre-compute consensus.
**Logic**:
    1.  **Drafting**: `gemini-2.0-flash` (Cost: 1x) generates the initial debate.
    2.  **Variance Check**: If `flash` agents agree (Confidence > 0.9), **COMMIT**.
    3.  **Escalation**: Only if `flash` agents disagree or have low confidence, wake up `gemini-2.0-pro` (Cost: 10x) to arbitrate.
*   **Optimization**: Most routine decisions are handled by the "Shadow Cabinet" at 10% cost.

### Pattern E: Impact-Aware Routing (The "Blast Radius" Check)
**Concept**: User intent is deceptive. "Just fixing a typo" in a core utility file can break the entire system.
**Logic**: Voting necessity is determined by **User Intent** AND **Code Impact**.

| Intent Risk | Blast Radius (Dep Graph) | Gov Level | Mode |
| :--- | :--- | :--- | :--- |
| Low (Typo) | Low (Leaf node) | **Level 0** | **Fast Track** (Direct Commit, No Vote) |
| Low (Typo) | High (Core Util) | **Level 1** | **Shadow Check** (1-Pass Review) |
| High (Refactor)| Low (Leaf node) | **Level 1** | **Shadow Check** (Flash Debate) |
| High (Refactor)| High (Core Util) | **Level 2** | **Full Council** (Pro Debate + Wald) |

*   **Implementation**: The `Architect` agent runs a dependency check (`git grep` or AST parsing) *before* the router decides to convene the council.


---

## 3. Comparison & Gap Analysis: Project `caicai`

| Feature | `caicai` Current State | 2025 Best Practice | Gap Severity |
| :--- | :--- | :--- | :--- |
| **Routing** | **Regex Adaptive** (`AdaptiveRouter`) | **Semantic + History Adaptive** | Medium |
| **Context** | **Append-Only** (`Facilitator` keeps full rounds) | **Rolling Summary / Differential** | **High (Token Leak)** |
| **Response** | **Natural Language + JSON** (Hybrid) | **Strict Schema / Bitmask** | Medium |
| **Memory** | **Dump-All** (`TaskLedger.to_context`) | **Lazy Loading (ID-based)** | **High (Token Leak)** |
| **Consensus** | **Wald SPRT** (Sequential) | **Speculative Parallel** (Flash -> Pro) | Low (Wald is robust) |

### Key Deficiency Identification
1.  **The "Dump-All" Problem**: `TaskLedger.to_context()` dumps all facts/queries/plans. As the project grows, this will hit context limits and wallet limits.
2.  **The "Infinite Scroll" Problem**: `Facilitator` appends rounds. A 10-round debate will eat exponential tokens (since each round repeats the previous history in the prompt).

---

## 4. Implementation Recommendations (Priority Order)

### Phase 1: Context Hygiene (Immediate Token Savings)
1.  **Modify `Facilitator`**: Implement **Rolling Summaries**.
    *   After Round 2, call `Summarizer` (Flash model) to compress R1.
    *   Prompt = `System + Task + Summary(History) + LastRound`.
2.  **Modify `DualLedger`**: Implement **Lazy Facts**.
    *   If `known_facts` > 5 items, summarize them into a list of "Headlines".
    *   Provide `get_fact_details()` tool.

### Phase 2: Protocol Communication
1.  **Update `Architect` and Agents**: Change `vote()` tool to accept structured Enums rather than free-text `rationale` as the primary driver.
2.  **Schema Enforcement**: Use Pydantic to force Agent outputs to be minimal.

### Phase 3: Speculative Execution (Cost Optimization)
1.  **Update `AdaptiveRouter`**: Add a `ShadowMode`.
2.  **Logic**: Try `Flash` swarm first. If `Wald.score` > Threshold, skip `Pro`.

---

## 5. Architectural Diagram (2025 Token-Efficient)

```mermaid
graph TD
    User[User Input] --> Router{Adaptive Router}
    
    %% Paths
    Router -- "Low Risk" --> M_Flash[Single Model (Flash)]
    Router -- "Med Risk" --> Shadow[Shadow Cabinet (Flash Swarm)]
    Router -- "High Risk" --> Full[Full Council (Pro/Ultra)]
    
    %% Shadow Logic
    subgraph Shadow Cabinet
        S_Arch[Arch (Flash)]
        S_Sec[Sec (Flash)]
        S_Gen[Consensus Check]
    end
    
    Shadow --> S_Gen
    S_Gen -- "Consensus Reached" --> Commit[Commit Action]
    S_Gen -- "Disagreement" --> Escalation[Escalate to Full Council]
    
    %% Context Management
    Ledger[(Lazy Ledger)] -. "Ref IDs Only" .-> Full
    Summarizer[Rolling Summarizer] -. "Compressed History" .-> Full
    
    Full --> Commit
```
