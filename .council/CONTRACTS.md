# API Contracts

> **SSOT**: 此文件是 API 契约的唯一真实来源。修改契约需同步更新测试和 DECISIONS.md。

## calculator.divide(a, b)

| 属性 | 描述 |
|------|------|
| **Domain** | `a: int\|float`, `b: int\|float` |
| **Behavior** | Returns `a / b` |
| **Errors** | `b == 0` → `ZeroDivisionError("division by zero")` |
| **Returns** | `float` |

### Contract Enforcement

- 契约由 `tests/test_contracts.py` 强制执行
- 变更契约必须：
  1. 更新本文档
  2. 更新 `tests/test_contracts.py`
  3. 在 `.council/DECISIONS.md` 记录原因

---

## calculator.add(a, b)

| 属性 | 描述 |
|------|------|
| **Domain** | `a: int\|float`, `b: int\|float` |
| **Behavior** | Returns `a + b` |
| **Errors** | None |

---

## calculator.subtract(a, b)

| 属性 | 描述 |
|------|------|
| **Domain** | `a: int\|float`, `b: int\|float` |
| **Behavior** | Returns `a - b` |
| **Errors** | None |

---

## calculator.multiply(a, b)

| 属性 | 描述 |
|------|------|
| **Domain** | `a: int\|float`, `b: int\|float` |
| **Behavior** | Returns `a * b` |
| **Errors** | None |
