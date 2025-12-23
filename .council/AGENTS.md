# Agent Council Governance (2025.12 最佳实践)

> **SSOT**: 多智能体协作治理规则

## 模型能力矩阵 (2025.12.24 研究)

| 模型 | 最强能力 | SWE-bench | 适用场景 |
|------|----------|-----------|----------|
| **Gemini 3 Pro** | UI/前端开发 | 未公开 | 视觉设计、Web 应用、多模态 |
| **Gemini 3 Flash** | 快速代码生成 | 78% | TDD 实现、迭代开发、高频工作流 |
| **GPT-5.2-Codex** | 代码审查/安全 | 高 | PR 审查、重构、安全扫描 |
| **Claude 4.5 Opus** | 规划/工程设计 | 80.9% | 架构设计、长任务规划、复杂推理 |
| **Claude 4.5 Sonnet** | 平衡性能 | 77.2% | 日常编码、快速审查 |

## 角色分工 (优化 Claude Token 使用)

```
┌─────────────────────────────────────────────────────┐
│                   开发流程                           │
├─────────────────────────────────────────────────────┤
│  1. BRIEF → 2. PLAN → 3. IMPL → 4. VERIFY → 5. SHIP │
│                                                     │
│  Claude 4.5     Gemini 3    Codex      just verify  │
│  Opus (规划)    Flash (TDD+实现)  (审查)  (门禁)      │
└─────────────────────────────────────────────────────┘
```

### 角色定义

| 角色 | 模型 | 职责 | Token 策略 |
|------|------|------|------------|
| **Architect** | Claude 4.5 Opus | PRD、任务拆分、架构决策 | 仅规划阶段使用 |
| **Implementer** | Gemini 3 Flash | TDD 红灯->绿灯、快速迭代 | 高频使用 |
| **Frontend** | Gemini 3 Pro | UI/UX、视觉设计、Web 应用 | 前端任务 |
| **Reviewer** | GPT-5.2-Codex | PR 审查、安全扫描、重构 | 提交前审查 |
| **Gate** | `just verify` | 本地门禁、唯一裁决 | 每次提交 |

## Token 节省策略

1. **Claude 仅做规划**：只在任务开始时使用 Claude 做 PRD/拆分
2. **Gemini Flash 做实现**：TDD、代码生成、迭代修复全部用 Gemini 3 Flash
3. **Codex 做审查**：最终审查、安全扫描用 Codex
4. **大任务拆小**：每个分支 < 1 小时，减少上下文

## Hard Safety Boundaries (Non-negotiable)

- DO NOT read, print, or exfiltrate secrets: .env, *.pem, *key*, credentials
- DO NOT run destructive commands (rm -rf, format disk, chmod -R on system paths)
- All changes must be reviewable (diff-first), reversible (git), and test-verified

## Definition of Done (DoD)

- [ ] Tests added/updated (TDD)
- [ ] `just verify` pass
- [ ] NOTES updated
- [ ] If architecture changed: DECISIONS entry added
