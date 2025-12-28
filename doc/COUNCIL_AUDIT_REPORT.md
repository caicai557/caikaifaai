# Council Architecture: Comprehensive Audit Report (2025.12.28)

> **Scope**: Deep comparison of Documentation vs. Implementation
> **Status**: ⚠️ Significant Gaps Identified

---

## 1. Documentation Inventory

| Document | Purpose | Status |
| :--- | :--- | :--- |
| `doc/GOVERNANCE_BEST_PRACTICES.md` | Phase 9 Blueprint (FSM, Constitution, Six Hats) | **Blueprint Only** |
| `doc/COUNCIL_2025_TOKEN_EFFICIENCY.md` | 2025 Token Optimization (Rolling Context, Shadow Cabinet) | **Research Complete** |
| `doc/COUNCIL_2025_IMPLEMENTATION_POC.md` | POC Code for 2025 Patterns | **POC Ready** |
| `doc/progress.md` | Project Progress Log | **Up to Date** |

---

## 2. Implementation Inventory

| Component | File | Status | Notes |
| :--- | :--- | :--- | :--- |
| **Wald Consensus** | `council/facilitator/wald_consensus.py` | ✅ **Implemented** | Robust SPRT logic. |
| **Facilitator** | `council/facilitator/facilitator.py` | ✅ **Implemented** | Manages rounds, BUT appends full history (Token Leak). |
| **Adaptive Router** | `council/orchestration/adaptive_router.py` | ✅ **Implemented** | Regex-based risk assessment. Lacks **Blast Radius**. |
| **Dual Ledger** | `council/orchestration/ledger.py` | ✅ **Implemented** | `to_context()` dumps all facts (Token Leak). |
| **Base Agent / Architect** | `council/agents/*.py` | ✅ **Implemented** | Uses NL prompts, not Protocol Buffers. |
| **MCP Server** | `council/mcp/ai_council_server.py` | ✅ **Implemented** | Semantic Routing + Wald + Governance Gateway. Good foundation. |
| **Governance Gateway** | `council/governance/gateway.py` | ✅ **Implemented** | PII Filtering, Risk Scanning. |
| **Constitution (FSM Interceptor)** | `council/governance/constitution.py` | ❌ **NOT IMPLEMENTED** | **Referenced in `GOVERNANCE_BEST_PRACTICES.md` but file does not exist!** |
| **Speaker FSM** | N/A | ❌ **NOT IMPLEMENTED** | Documented as Phase 9, Step 2. Not started. |
| **Six Thinking Hats** | N/A | ❌ **NOT IMPLEMENTED** | Documented as Pattern C. Not started. |
| **Rolling Context** | N/A | ❌ **NOT IMPLEMENTED** | In POC only. |
| **Shadow Cabinet** | N/A | ❌ **NOT IMPLEMENTED** | In POC only. |
| **Blast Radius Analyzer** | N/A | ❌ **NOT IMPLEMENTED** | In POC only. |

---

## 3. Critical Discrepancies (Doc vs. Code)

### 3.1. `GOVERNANCE_BEST_PRACTICES.md` References Non-Existent File
*   **Doc Says**: `Implementation: src/telegram_multi/cortex/governance/constitution.py`
*   **Reality**: `council/governance/` only contains `__init__.py` and `gateway.py`. **No `constitution.py` exists.**
*   **Impact**: The entire "Benevolent Bureaucracy" (FSM Speaker, Constitution Interceptor) section is **vaporware**.

### 3.2. Token Leaks (Confirmed in Code)
*   **`Facilitator.process_round()`**: Appends `DebateRound` to `self.current_meeting.rounds` list. This means calls to `get_summary()` will include all prior rounds, causing **O(N)** context growth.
*   **`TaskLedger.to_context()`**: Iterates through `self.known_facts` and dumps everything. No lazy loading or summarization.

### 3.3. Agent Communication is Verbose
*   **`Architect.vote()` (Line 142-229)**: Uses a free-text `prompt` asking for `Vote: [DECISION]`, `Confidence: [0.0-1.0]`, `Rationale: [理由]`. The `rationale` field is unbounded natural language.
*   **Best Practice**: 2025 Protocol should use `MinimalVote(vote=1, risks=["security"])` and disallow verbose text.

---

## 4. Reconciliation Roadmap (Priority)

### Phase 0: Fix Dead References (Immediate)
1.  **Update `GOVERNANCE_BEST_PRACTICES.md`**: Change the `constitution.py` path from `src/telegram_multi/cortex/...` to `council/governance/...`.
2.  **Create Stub `constitution.py`**: Even if empty, the file should exist to avoid confusion.

### Phase 1: Context Hygiene (Medium Priority)
1.  **Integrate `RollingContext` into `Facilitator`**: Replace list append with the sliding window logic from POC.
2.  **Refactor `TaskLedger`**: Add `get_headlines()` and `get_fact_detail(id)` methods.

### Phase 2: Adaptive Routing (Medium Priority)
1.  **Integrate `BlastRadiusAnalyzer` into `AdaptiveRouter`**: The `route()` method should call `calculate_impact()` before deciding on `SINGLE_MODEL` vs `FULL_COUNCIL`.

### Phase 3: Protocol Communication (Lower Priority)
1.  **Define `MinimalVote` schema** in `council/protocol/schema.py`.
2.  **Refactor Agent `vote()` methods** to output strict JSON.

### Phase 4: Shadow Cabinet (Lower Priority)
1.  **Implement `ShadowFacilitator`** in production.
2.  **Wire `AdaptiveRouter` to use `ShadowMode`** for Medium-Risk tasks.

---

## 5. Summary

| Category | Grade | Justification |
| :--- | :--- | :--- |
| **Wald Consensus** | A | Fully implemented, mathematically sound. |
| **Semantic Routing** | B+ | Present in MCP Server (`_classify_request`), but could be more granular. |
| **Token Efficiency** | D | Major leaks in Facilitator and Ledger. Not addressed. |
| **Doc-Code Sync** | F | `constitution.py` reference is broken. FSM/Speaker not started. |
| **2025 Readiness** | C- | Concepts are documented and POC exists, but nothing is integrated. |

**Overall Verdict**: The **foundational components** (Wald, Agents, MCP Server) are **solid**, but the **governance layer** described in documentation is largely **unbuilt**. The 2025 Token Efficiency patterns are **designed but not deployed**. Immediate focus should be on **closing the Doc-Code gap** and **implementing Phase 1 (Context Hygiene)**.
