---
description: 2025 标准特性开发流 (Double II Framework)
---

# Phase 1: Information (Plan & Design)

1. 启动智能注入与规划
// turbo
./scripts/council_run.py --task "PLAN-${argument}" --goal "Planning for: ${argument}" --risk low --learn --dry-run

2. 审查架构设计与依赖

> [!IMPORTANT]
> 请仔细阅读上一步输出的 "Smart Injection" 和 "Relevant Lessons"。
> 结合 `.council/knowledge_graph.gml` 确认是否有架构冲突。

# Phase 2: Implementation (TDD & Code)

> [!CAUTION]
> **Token Saving Guard**: 在任何 Edit 操作前，必须检查：
>
> - Lint 错误？ → `ruff check --fix .`
> - 修改 ≥3 处？ → `python scripts/batch_replace.py`
> - 不确定方案？ → 先创建 `repro.py` 本地验证

1. 执行 TDD 循环 (Swarm Mode)
// turbo
./scripts/council_run.py --task "IMPL-${argument}" --goal "Implement feature: ${argument}" --risk medium --ephemeral

# Phase 3: Verification (Wald Score)

1. 运行 Wald 裁决
// turbo
./scripts/wald_score.py --risk medium

2. (可选) 如果 Wald 分数 < 0.95，自动启动自愈
// turbo
./scripts/council_run.py --task "FIX-${argument}" --goal "Fix Wald Score violations for ${argument}" --risk high
