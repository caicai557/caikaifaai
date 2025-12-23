# Architectural Decisions Log (ADL)

## ADL-001: 契约变更规则

- **Date**: 2025-12-24
- **Decision**: 任何异常类型/语义契约变化必须同时满足：
  1. 更新 `.council/CONTRACTS.md`
  2. 更新/新增 `tests/test_contracts.py`
  3. 在本文件记录原因与替代方案
- **Context**: 防止"悄悄改契约"导致 API 破坏性变更
- **Alternatives**: 无强制门禁（不推荐）
- **Consequences**: 保证契约变更可追溯、可审计

---

## ADL-002: divide() 异常类型选择

- **Date**: 2025-12-24
- **Decision**: `divide(a, b)` 在 `b == 0` 时抛出 `ZeroDivisionError`
- **Context**: 与 Python 原生行为一致（`1/0` 抛出 `ZeroDivisionError`）
- **Alternatives**:
  - `ValueError` - 语义为"非法参数"，但与生态不一致
  - 返回 `None` / `float('inf')` - 隐藏错误，不推荐
- **Consequences**:
  - 调用方可用 `except ZeroDivisionError` 捕获
  - 与 Python 标准行为一致，学习成本低
