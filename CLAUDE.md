# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

> [!IMPORTANT]
> **Strictly follow the rules in [.council/AGENTS.md](./.council/AGENTS.md)**

## Project Overview

**Name**: cesi-council
**Type**: Python backend application (Multi-Agent Council Framework)
**Main Purpose**: Multi-agent orchestration system for AGI development workflows
**Language**: Python 3.12+
**Architecture**: Hierarchical Supervision with Wald Consensus + PTC (Programmatic Tool Calling)

## Common Commands

### Development Commands

```bash
# Install dependencies
pip install -e ".[dev]"              # Development tools (pytest, ruff)
pip install -e ".[council]"          # Council features (LLM integrations)

# Testing
just test                            # Run pytest on tests/ directory
pytest tests/test_<module>.py        # Run single test file

# Code quality
just lint                            # Check code with ruff
just compile                         # Check syntax with py_compile

# Verification
just verify                          # Run compile + lint + test (gate keeper)
just ship                            # verify + codex review + show git log
```

### Development Workflow

```bash
just dev "<task description>"        # Full workflow: Six Step Self-Healing Loop
# 1. Codex: Requirement Codification (PRD/Task Tree)
# 2. Gemini: Audit & Design (Code Map)
# 3. Claude: TDD Gate (tests.json)
# 4. Claude: PTC Execution (Code Mode)
# 5. Wald: Self-Healing & Consensus
# 6. Gemini: Checkpoint & Archival
just tdd                             # TDD mode (write tests first)
just impl                            # Implementation mode (minimal patch + verify)
```

## Architecture & Code Organization

### Core Modules

```text
src/
├── config.py                 # Global feature flags
└── calculator.py             # Utility module

council/
├── agents/                   # Agent implementations
│   ├── base_agent.py         # Abstract base class + _call_llm_structured()
│   ├── architect.py          # Architect + vote_structured()
│   ├── coder.py              # Engineer + vote_structured()
│   └── security_auditor.py   # Security audit + vote_structured()
├── facilitator/              # Consensus mechanisms
│   ├── facilitator.py        # Debate management + RollingContext
│   ├── wald_consensus.py     # SPRT algorithm
│   └── shadow_facilitator.py # Shadow cabinet (speculative consensus)
├── orchestration/            # Orchestration layer
│   ├── adaptive_router.py    # Adaptive routing + BlastRadius
│   ├── ledger.py             # Dual ledger (Task/Progress)
│   └── blast_radius.py       # Code impact analyzer
├── governance/               # Governance layer
│   ├── constitution.py       # FSM rule interceptor
│   └── gateway.py            # Output filter gateway
├── protocol/                 # Communication protocol
│   └── schema.py             # Pydantic structured protocol
├── context/                  # Context management
│   └── rolling_context.py    # Sliding window context
├── memory/                   # Long-term memory
│   ├── knowledge_graph.py    # Semantic relationship graph
│   └── session.py            # Cross-session context
└── self_healing/             # Self-healing loop
    └── patch_generator.py    # LLM-driven patch generation
```

### Key Classes & Patterns

**BaseAgent** (`council/agents/base_agent.py`):

- Abstract base class for all council agents
- Provides `_call_llm_structured()` for structured LLM calls
- Implements `vote_structured()` for consensus voting

**WaldConsensus** (`council/facilitator/wald_consensus.py`):

- Sequential Probability Ratio Test (SPRT) implementation
- Dynamic decision: COMMIT / CONTINUE / STOP

**AdaptiveRouter** (`council/orchestration/adaptive_router.py`):

- Risk-based routing to appropriate agents
- BlastRadius analysis for change impact

## Testing Strategy

- **Framework**: Pytest with coverage tracking
- **Test Structure**: One test file per source module
- **Mocking**: Use `unittest.mock` for LLM and external service mocks
- **Run**: `just test` or `pytest tests/` for all tests

## Development Standards

- **Type Hints**: Required for all function signatures
- **Async/Await**: Used for LLM calls and I/O operations
- **Config**: Use Pydantic models for configuration
- **Providers**: Use factory pattern for pluggable LLM providers

## Batch Operations Protocol

For changes affecting 3+ files, write a Python script instead of manual edits:

```python
# Example: scripts/bulk_rename.py
import os, re, glob
for filepath in glob.glob("src/**/*.py", recursive=True):
    with open(filepath) as f:
        content = f.read()
    content = re.sub(r"old_name", "new_name", content)
    with open(filepath, "w") as f:
        f.write(content)
```

## Token Saving Rules (MANDATORY)

> [!CAUTION]
> **违反以下规则将被视为严重错误。每次 Edit ≈ 3k tokens，批量工具 ≈ 0.5k tokens。**

### 强制规则

1. **Lint 错误必须用自动修复**:

   ```bash
   ruff check --fix .                    # 不要逐个 Edit
   ruff check --select E501 --fix .      # line-too-long
   black .                               # 格式化
   isort .                               # import 排序
   ```

2. **修改 ≥3 处相同代码必须用批量脚本**:

   ```bash
   python scripts/batch_replace.py -p "old" -r "new" -g "src/**/*.py"
   ```

3. **不确定方案时必须先本地验证**:

   ```bash
   # 创建 repro.py 验证方案，确认可行后再 Edit
   python repro.py
   ```

### 检查清单 (每次 Edit 前)

- [ ] 这是 lint 错误吗？ → **用 ruff/black**
- [ ] 需要修改 ≥3 处吗？ → **用批量脚本**
- [ ] 我确定方案能工作吗？ → **先本地验证**

## Verification Gate (just verify)

This is the single arbiter of quality:

1. `compile`: Check Python syntax
2. `lint`: Check code style with ruff
3. `test`: Run pytest suite

All three must pass before shipping.

## Safety Boundaries

- ❌ **Forbidden**: `rm -rf`, `git push`, modifying `.env`, destructive file operations
- ✅ **Free**: `read`, `ls`, `grep`, `lint`, `pytest`, `python -m py_compile`
- ⚠️ **Confirm**: Git commits/pushes, file deletions, batch edits

## Related Documentation

- [.council/AGENTS.md](./.council/AGENTS.md): Agent governance and routing rules
- [CODEMAP.md](./CODEMAP.md): High-level project architecture
- [NOTES.md](./NOTES.md): Session notes and decisions
- [pyproject.toml](./pyproject.toml): Project metadata and dependencies

## 理事会层级监督指令集 (2025.12.26)

## 编排协议 (Orchestration)

- 优先查阅 `Task Ledger`，所有决策需锚定在 `AGENTS.md` 定义的规则之内。
- 在大型重构前，强制调用 `gemini-think` 进行 2M 上下文全库审计。

## 执行约束 (Execution)

- 涉及 3 步以上的操作必须使用 PTC 脚本编排，禁用逐条自然语言确认。
- 代码实施前必须先在 `/tests/` 目录下建立 Red 状态的测试用例。

## 记忆管理 (Persistence)

- 会话接近上限时，自动调用 `/compact` 总结架构决策并归档至 `NOTES.md`。
- 任务结束前，必须提供一段包含逻辑差异与风险提示的最终总结。
