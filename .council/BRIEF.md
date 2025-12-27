# BRIEF (Single Source of Truth)

> 当前开发任务的单一事实来源

## 项目

**cesi-telegram-multi**: Telegram Web A 多开 + 双向自动翻译

## 当前任务

**测试覆盖率提升：70% → 90%**

## 问题陈述

- **当前状态**: 测试覆盖率 70%（240 stmts, 71 miss），未达到门禁要求（≥90%）
- **目标状态**: 覆盖率 ≥90%，关键模块 100%，`just verify` 通过
- **非目标**: 不做集成测试、不做性能测试、不做 E2E 测试（仅单元测试）

## 用户故事

作为开发者，
我希望测试覆盖率 ≥90%，
以便确保代码质量和防止回归。

## 验收标准

- [ ] AC1: 总覆盖率 ≥90%
- [ ] AC2: `src/config.py` 覆盖率从 0% → 100%
- [ ] AC3: `message_interceptor.py` 从 69% → 100%
- [ ] AC4: `translators/google.py` 从 29% → 90%
- [ ] AC5: `just verify` 通过（含覆盖率检查）

## 当前覆盖率分析

| 模块 | 当前覆盖 | 目标 | 缺失行数 | 优先级 |
|------|---------|------|---------|--------|
| **src/config.py** | 0% (0/20) | 100% | 20 | 🔴 P0 |
| **translators/google.py** | 29% (12/41) | 90% | 29 | 🔴 P0 |
| **message_interceptor.py** | 69% (35/51) | 100% | 16 | 🟡 P1 |
| **translator.py** | 87% (27/31) | 100% | 4 | 🟢 P2 |
| **instance_manager.py** | 96% (27/28) | 100% | 1 | 🟢 P2 |
| **telegram_multi/config.py** | 98% (47/48) | 100% | 1 | 🟢 P2 |

**缺失覆盖总计**: 71 行 → 目标：≤24 行（90% 覆盖需 216/240 已测）

## 任务树

```
5.1 修复 P0 高优先级模块
    ├── 5.1.1 [tests/test_config.py] 补充 src/config.py 测试 (20 行)
    └── 5.1.2 [tests/test_translators_google.py] 补充异常路径 (29 行)

5.2 修复 P1 中优先级模块
    └── 5.2.1 [tests/test_message_interceptor.py] 补充边界测试 (16 行)

5.3 修复 P2 低优先级模块
    ├── 5.3.1 [tests/test_translator.py] 补充异常处理 (4 行)
    ├── 5.3.2 [tests/test_instance_manager.py] 补充边界条件 (1 行)
    └── 5.3.3 [tests/test_telegram_config.py] 补充错误路径 (1 行)

5.4 验证与提交
    ├── 运行 `just verify` 确认 ≥90%
    └── 更新 .council/NOTES.md
```

**复杂度估算**:

- 5.1: 中等（需要理解未测代码逻辑）
- 5.2: 简单（已有测试框架，补充用例）
- 5.3: 简单（边界修补）
- 5.4: 简单（验证）

## 模型分发建议

| 阶段 | 模型 | 命令 | 理由 |
|------|------|------|------|
| TDD | Gemini 3 Flash | `/tdd "5.1.1 config.py 测试"` | 高频测试编写，速度快 |
| 实现 | Gemini 3 Flash | `/impl "5.1.1 补充测试"` | 快速迭代 |
| 审查 | Codex 5.2 | `/review` | 质量把关 |
| 验证 | - | `just verify` | 自动化门禁 |

## 下游命令

```bash
# 步骤 1: TDD 补充测试
/tdd "5.1.1 src/config.py 测试覆盖"

# 步骤 2: 实现测试
/impl "5.1.1 补充 config.py 单元测试"

# 步骤 3: 验证覆盖率
just verify

# 步骤 4: 代码审查
/review

# 步骤 5: 提交
/checkpoint "测试覆盖率提升至 90%"
```

## 技术细节

### 缺失测试用例分析

1. **src/config.py** (0% 覆盖)
   - 缺失：类初始化、方法调用、异常处理
   - 需要：完整单元测试套件

2. **translators/google.py** (29% 覆盖)
   - 缺失：重试逻辑、异常处理、速率限制
   - 缺失行：43-83, 98-106

3. **message_interceptor.py** (69% 覆盖)
   - 缺失：错误路径、边界条件
   - 缺失行：87-98, 115-137

### 测试策略

- **优先级**: P0 → P1 → P2（先解决高覆盖缺口）
- **方法**: 补充异常路径、边界条件、错误处理
- **原则**: 最小测试集（避免过度测试）
