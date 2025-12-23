# BRIEF (Single Source of Truth)

## Goal

- **当前任务**: 修复 `src/calculator.py` 中 `divide()` 函数的除零 bug
- 当 `b=0` 时应抛出 `ValueError` 而非让 Python 抛出 `ZeroDivisionError`
- 同时补充对应的测试用例

## Constraints

- **安全**: 不修改任何配置文件或安装新依赖
- **范围**: 仅修改 `src/calculator.py` 和 `tests/test_calculator.py`
- **代码量**: 变更 < 20 行 (符合小 PR 原则)
- **Non-goals**: 不重构其他模块，不添加新功能

## Current Architecture

```
cesi.worktrees/
├── src/
│   ├── __init__.py
│   ├── config.py      # 功能开关管理
│   └── calculator.py  # 四则运算 (有 bug)
├── tests/
│   ├── __init__.py
│   └── test_calculator.py  # 测试用例 (缺少边界测试)
├── .council/           # Agent Council 治理文件
├── scripts/            # 工具脚本
└── Justfile           # 工作流命令
```

## Acceptance Criteria

- [ ] `divide(5, 0)` 抛出 `ValueError` 并包含友好错误信息
- [ ] `test_divide_by_zero` 测试通过
- [ ] 所有现有测试仍然通过
- [ ] 代码无 lint 错误

## Commands

```bash
# 运行测试
pytest tests/ -v

# 运行单个测试
pytest tests/test_calculator.py -v

# 代码检查 (如果有)
python -m py_compile src/calculator.py
```
