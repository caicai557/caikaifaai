# Exception Contracts（异常契约）

> SSOT：所有异常类型的契约定义

## 1. 输入校验（可恢复）

- **违反前置条件**: 抛 `ValueError` / `TypeError`
- **必须包含**: 参数名 + 期望范围 + 实际值摘要

```python
# 示例
raise ValueError(f"b must be non-zero, got {b}")
```

## 2. 业务异常（可恢复）

- **除零错误**: `ZeroDivisionError("division by zero")`
- **必须稳定**: error_code、message、可选 detail

## 3. 外部依赖失败（可能可恢复）

- **网络/第三方 API**: 抛 `TransientError`（或带 `retryable=true`）
- **必须**: 是否可重试、重试退避建议

## 4. 不可恢复错误

- **数据损坏/不变量破坏**: Fail-fast（禁止吞异常）

---

## 函数契约

### calculator.divide(a, b)

| 属性 | 描述 |
|------|------|
| **Domain** | `a: int\|float`, `b: int\|float` |
| **Behavior** | Returns `a / b` |
| **Errors** | `b == 0` → `ZeroDivisionError("division by zero")` |
| **Returns** | `float` |

### calculator.add(a, b)

| 属性 | 描述 |
|------|------|
| **Domain** | `a: int\|float`, `b: int\|float` |
| **Behavior** | Returns `a + b` |
| **Errors** | None |

### calculator.subtract(a, b)

| 属性 | 描述 |
|------|------|
| **Domain** | `a: int\|float`, `b: int\|float` |
| **Behavior** | Returns `a - b` |
| **Errors** | None |

### calculator.multiply(a, b)

| 属性 | 描述 |
|------|------|
| **Domain** | `a: int\|float`, `b: int\|float` |
| **Behavior** | Returns `a * b` |
| **Errors** | None |

---

## Contract Enforcement

- 契约由 `tests/test_contracts.py` 强制执行
- 变更契约必须：
  1. 更新本文档
  2. 更新 `tests/test_contracts.py`
  3. 在 `.council/DECISIONS.md` 记录原因
