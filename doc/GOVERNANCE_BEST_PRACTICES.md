# Agent Council Governance: Best Practices (2025 Edition)

> **Context**: This document outlines the architectural standards for the `cesi-telegram-multi` Agent Council.
> **Source**: Phase 9 Research Findings.

## 1. The Philosophy: "Benevolent Bureaucracy" (仁慈的官僚主义)

In advanced Multi-Agent Systems, pure autonomy leads to entropy. We adopt a **Federated Governance** model where freedom is exercised within strict constitutional bounds.

### Core Tenants
1.  **Immutability**: The "Blackboard" (Context) must be immutable and audible (SQLite WAL).
2.  **Separation of Powers**: The Actor proposing a plan (Legislative) cannot be the one executing it (Executive) without explicit consensus (Judicial).
3.  **Finite State Machine (FSM)**: Conversations are not infinite streams; they are state transitions (`PROPOSE` -> `VOTE` -> `ACT`).

## 2. Design Patterns

### Pattern A: The Constitution (规则拦截器)
**Definition**: A static, hard-coded ruleset that runs *before* any LLM inference.
**Implementation**: `src/telegram_multi/cortex/governance/constitution.py`

*   **Rule 1 (Safety)**: No destructive shell commands (`rm`, `dd`) allowed without `sudo_token`.
*   **Rule 2 (Order)**: Agents cannot interrupt `Speaker` during a `VOTING` phase.
*   **Code Reference**:
    ```python
    def validate_action(action: dict, state: str) -> bool:
        if state == "VOTING" and action["type"] != "VOTE":
            return False
        return True
    ```

### Pattern B: The Speaker (议长/Speaker)
**Definition**: A specialized Actor responsible for managing the `ConversationGraph`.
**Role**:
*   Assigns "The Chalk" (Turn-taking) to agents.
*   Detects Consensus (Super-Majority or Unanimity).
*   Enforces Timeouts (preventing filibusters).

### Pattern C: The "Six Thinking Hats" (六顶思考帽)
**Definition**: Dynamic Persona Injection.
To prevent "Agent Halos" (agents agreeing with everything), we forcibly inject conflicting system prompts during debate.
*   🔴 **Red Hat**: The Critic. MUST find 3 flaws.
*   🟢 **Green Hat**: The Innovator. MUST propose 1 alternative.
*   🔵 **Blue Hat**: The Moderator. MUST summarize the current state.

## 3. Implementation Roadmap (Phase 9)

### Step 1: Constitution
Create `constitution.py` to act as the "Gatekeeper" for `AgentActor.handle()`.

### Step 2: Speaker Actor
Create `SpeakerActor` (inheriting from `BaseActor`) to replace the basic loop in `CouncilActor`.

### Step 3: Voting Logic
Agents will gain a `vote` tool.
*   `vote(approval=True, reasoning="...")`
*   Speaker tallies votes in `CortexDB` (`votes` table).

## 4. Technical Implementation Specifications (技术实现细节)

### A. Database Schema: The Ballot Box

We will add a `votes` table to `CortexDB` to make every decision audit-proof.

```sql
CREATE TABLE IF NOT EXISTS votes (
    id TEXT PRIMARY KEY,
    trace_id TEXT NOT NULL,         -- Links to the discussion context
    round_id INTEGER NOT NULL,      -- Voting round (1, 2, 3...)
    voter_agent TEXT NOT NULL,      -- Who voted (e.g. 'Coder')
    choice TEXT NOT NULL,           -- 'APPROVE', 'REJECT', 'ABSTAIN'
    reasoning TEXT,                 -- Why they voted this way
    timestamp REAL NOT NULL
);
CREATE INDEX idx_votes_trace_round ON votes(trace_id, round_id);
```

### B. The Speaker FSM (Finite State Machine)

The Speaker Actor is not just an LLM; it is a **State Machine** wrapper around an LLM.

| State | Trigger | Action | Next State |
| :--- | :--- | :--- | :--- |
| **IDLE** | User Input | Broadcast `THINK` task to Architect | `DEBATING` |
| **DEBATING** | Agents reply | Log replies, check for keywords | `DEBATING` / `VOTING` |
| **DEBATING** | Silence/Timeout | Ask: "Are we ready to vote?" | `VOTING` |
| **VOTING** | `vote()` tool | Record vote in DB | `VOTING` |
| **VOTING** | Consensus Reached | Broadcast `EXECUTE` command | `EXECUTING` |
| **EXECUTING** | Tool Result | Summarize outcome | `IDLE` |

### C. The Consensus Algorithm: Wald SPRT (Simplified)

Instead of waiting for *everyone* to vote (which is slow) or just 51% (which is risky), we use a sequential test to stop voting early if the outcome is statistically certain.

```python
def check_consensus(votes: List[bool], alpha=0.05, beta=0.05) -> str:
    """
    Wald Sequential Probability Ratio Test.
    Returns: 'ACCEPT', 'REJECT', or 'CONTINUE'
    """
    # H0: p = 0.5 (Random/Controversial)
    # H1: p = 0.8 (Strong Consensus)
    
    score = 0.0
    for v in votes:
        if v: score += log(0.8/0.5) # Approvals boost score
        else: score += log(0.2/0.5) # Rejections penalty score
        
    upper_bound = log((1-beta)/alpha)
    lower_bound = log(beta/(1-alpha))
    
    if score > upper_bound: return 'ACCEPT'
    if score < lower_bound: return 'REJECT'
    return 'CONTINUE'
```

### D. The Constitution (Interceptor Logic)

The `Constitution` class acts as a middleware in the message loop.

```python
class Constitution:
    def check(self, msg: dict) -> bool:
        # Rule: Agents cannot speak out of turn during voting
        if self.speaker_state == "VOTING" and msg.get("tool") != "vote":
            raise Violation("Silence in court! Only votes are allowed now.")
        
        # Rule: No repetition
        if self._is_repetitive(msg["content"]):
            raise Violation("Do not repeat yourself. Add new information.")
            
        return True
```

