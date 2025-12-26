---
description: 深度调试模式 (Think Pattern)
---

# Step 1: Context Gathering

1. 收集错误上下文与关联代码
// turbo
./scripts/knowledge_base.py search "${argument}"

2. 构建当前依赖图
// turbo
./scripts/graph_builder.py build

# Step 2: Thinking (CoT)

3. 深度分析

> [!NOTE]
> 请基于收集到的上下文，在 `<thinking>` 标签中详细推演 Bug 的根因。
> 不要直接生成代码，先列出 3 个可能的假设，并设计验证方案。

# Step 3: Execution

4. 执行修复 Swarm
// turbo
./scripts/council_run.py --task "DEBUG-${argument}" --goal "Fix bug based on analysis: ${argument}" --risk high --ephemeral

# Step 4: Verification

5. 验证修复
// turbo
./scripts/wald_score.py --risk high
