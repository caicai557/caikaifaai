---
description: 模型委托 — 特殊场景委托工具
argument-hint: <模型> <任务>
---

# 模型委托 (扩展命令)

**⚠️ 注意**: 这是扩展命令，仅用于特殊场景。标准流程请使用六步循环命令。

## 何时使用

**优先使用标准命令**：
- PM 规划 → `/plan`
- 架构审计 → `/audit`
- TDD 测试 → `/tdd`
- 最小实现 → `/impl`
- 验证裁决 → `/verify`
- 代码审查 → `/review`

**仅在以下特殊场景使用 `/delegate`**：
- 需要直接与特定模型交互（绕过标准流程）
- 实验性任务（不属于标准六步流程）
- 快速原型验证

## 用法
```bash
/delegate gemini <task>   # 委托给 Gemini
/delegate codex <task>    # 委托给 Codex
```

## 任务
$ARGUMENTS

## 模型能力

| 模型 | 适用场景 |
|------|----------|
| Gemini Pro | 全库审计 (2M 上下文)、前端开发 |
| Gemini Flash | 快速迭代、原型开发 |
| Codex | 代码修复、精确对齐 |

## 委托给 Gemini

```bash
# 审计 (Pro)
gemini -m pro "审计: <task>. 读取 CODEMAP.md."

# TDD/实现 (Flash)
gemini -m flash "TDD: <task>. 先写测试,覆盖率 ≥90%."
```

## 委托给 Codex

```bash
# 代码审查
codex "审查: <task>. 输出风险点+精确位置+修复建议."

# 修复/对齐
codex "修复: <task>. 最小 patch, 边界对齐."
```

## 输出要求

1) 生成的命令 (可直接执行)
2) 预期返回内容
3) 如何将结果带回 Claude 会话
