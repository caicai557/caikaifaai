# Iteration Notes (Session Summary)

## 2025-12-24 Session

### SOP 完整流程执行记录

**任务**: 修复 `divide()` 除零 bug

| 阶段 | 状态 | 产出 |
|------|------|------|
| Plan | ✅ | 实施计划，用户批准 |
| Audit | ✅ | 审计通过，无需修改 |
| TDD | ✅ | 测试先行，红灯验证 |
| Impl | ✅ | 修复代码，添加 `b==0` 检查 |
| Verify | ✅ | 5/5 测试通过 |
| Ship | ✅ | 提交完成 |

### 变更内容

- `src/calculator.py`: 添加除零检查，抛出 `ValueError`
- `tests/test_calculator.py`: 添加 `test_divide_by_zero` 测试

### 风险/后续

- 无遗留风险
- ✅ 已补齐边界测试矩阵

---

### 契约声明 (Contract)

| 函数 | 契约 |
|------|------|
| `divide(a, b)` | 当 `b==0` 时抛出 `ValueError("Cannot divide by zero")` |
| `divide(a, b)` | 接受 `float` 输入，返回 `float` |

### 测试矩阵

| 测试用例 | 断言 |
|----------|------|
| `divide(5, 0)` | `pytest.raises(ValueError, match="Cannot divide by zero")` |
| `divide(0, 5)` | 返回 `0` |
| `divide(-10, 2)` | 返回 `-5` (符号正确) |
| `divide(0.1, 0.1)` | `pytest.approx(1.0)` (浮点精度) |
