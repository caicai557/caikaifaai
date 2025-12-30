# Council Framework: Architecture Map (2025.12)

> **Core Vision**: Multi-Agent Council for AGI Development  
> **Package**: `council` (`cesi-council` v1.0.0)

## 1. Directory Structure

```
council/
├── agents/                   # [THE COUNCIL] Role-Specialized Agents
│   ├── architect.py          # System Design & Risk Assessment
│   ├── coder.py              # Code Implementation & TDD
│   ├── security_auditor.py   # Zero-Trust Security Auditor (Skeptic)
│   └── base_agent.py         # BaseAgent Protocol (think/vote/execute)
├── orchestration/            # [THE BRAIN] Task Routing & Delegation
│   ├── model_router.py       # LLM Selection (Cost/Capability)
│   ├── task_classifier.py    # Intent Classification
│   └── delegation.py         # Agent Assignment
├── persistence/              # [STATE] Multi-Backend Storage
│   ├── state_store.py        # SQLite (Local)
│   ├── redis_store.py        # Redis (Distributed + Locks)
│   └── checkpoint.py         # Session Snapshots
├── memory/                   # [LONG-TERM CONTEXT]
│   ├── vector_memory.py      # ChromaDB Vector Store
│   ├── rag_retriever.py      # Semantic Search
│   └── knowledge_graph.py    # Entity Relationships
├── tools/                    # [THE HANDS] Sandboxed Execution
│   └── programmatic_tools.py # AST-Validated Python Sandbox
├── streaming/                # [REALTIME]
│   └── sse_formatter.py      # Server-Sent Events
└── auth/                     # [SECURITY]
    └── rbac.py               # Role-Based Access Control
```

## 2. Role Specialization (2025 Best Practices)

### A. Architect (架构师)
*   **责任**: 顶层设计、风险识别、方案评审
*   **核心原则**: 长期可维护性 > 短期交付速度
*   **关键方法**:
    *   `think(task) -> ThinkResult`: 架构分析
    *   `vote(proposal) -> Vote`: 评审投票 (APPROVE/HOLD/REJECT)
    *   `think_structured()`: 2025 Token-Efficient 版本 (节省70%)

### B. Coder (工程师)
*   **责任**: 代码实现、测试编写、代码审查
*   **编码纪律**:
    *   Small Diffs (≤200 行/PR)
    *   TDD First (测试覆盖 ≥ 90%)
    *   防御性编程 (空值/异常/竞态)
*   **关键方法**:
    *   `generate_tests(spec)`: 自动生成测试
    *   `review_code(code)`: 代码审查

### C. SecurityAuditor (安全审计员) - **HARDENED PERSONA**
*   **角色**: **怀疑论者 (Skeptic)**
*   **原则**:
    *   ⚠️ **零信任**: 不给代码 "疑点利益"
    *   ⚠️ **最坏假设**: 所有输入都是恶意的
    *   ⚠️ **宁可误报**: False Positive > False Negative
*   **关键方法**:
    *   `scan_vulnerabilities(code)`: 静态漏洞扫描
    *   `check_sensitive_paths(paths)`: 敏感路径检查 (`.ssh/`, `.env`)
*   **系统提示 (摘录)**:
    > "You are a SKEPTIC. Your performance is measured by vulnerabilities FOUND, not code approved."

## 3. Orchestration Layer

| Component | File | Responsibility |
| :--- | :--- | :--- |
| **ModelRouter** | `orchestration/model_router.py` | 按成本/能力选择 LLM (Gemini/Claude/GPT) |
| **TaskClassifier** | `orchestration/task_classifier.py` | 意图分类 → 路由至对应 Agent |
| **DelegationManager** | `orchestration/delegation.py` | Agent 任务分配与同步 |

## 4. Security Best Practices (Implemented)

### A. Sandboxed Code Execution (`tools/programmatic_tools.py`)
*   **AST 验证**: 禁止 `os`, `sys`, `subprocess`, `eval`, `exec`
*   **安全内建**: 仅暴露安全函数 (`len`, `range`, `print`, 等)
*   **超时控制**: 默认 30s 超时

### B. RBAC & Sensitive Paths (`auth/rbac.py`)
*   **敏感路径黑名单**: `~/.ssh/*`, `~/.aws/*`, `*/.env`, `*/secrets/*`
*   **权限分级**: `read`, `write`, `execute`

## 5. Development Flows

### Run Tests
```bash
pytest tests/ -v
```

### Start CLI
```bash
council --help  # Entry point: council/cli.py
```

## 6. Version History

| Version | Status | Highlights |
| :--- | :--- | :--- |
| **1.0.0** | **Current** | Role Specialization, Structured Output, Sandboxed Tools |
| 0.3.0 | Legacy | Initial MCP Integration |
