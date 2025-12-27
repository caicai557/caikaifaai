---
description: 全库审计 — 扫描代码库、发现冲突 (Gemini Pro)
argument-hint: [范围或功能]
---

# 架构审计 (2025 Optimized)

**主控**: Gemini 3 Pro (2M 上下文)

## 任务
$ARGUMENTS

## 执行流程

1) 扫描范围确定
   - 读取 CODEMAP.md 了解架构
   - 确定影响的模块 (≥3 模块时必用此命令)

2) 冲突检测
   - 新旧逻辑冲突
   - API 契约变化
   - 依赖兼容性

3) 输出设计文档
   ```yaml
   audit_report:
     conflicts: [...]      # 冲突列表 (severity + location)
     design_decisions: [...] # 设计决策 + rationale
     risks: [...]          # 风险点 (≤5条)
     next_steps: [...]     # 后续步骤
   ```

4) 委托执行
   ```bash
   gemini -m pro "审计: $ARGUMENTS. 扫描 CODEMAP.md 和相关模块."
   ```

## 触发条件

满足任一:
- [ ] 影响 ≥3 模块
- [ ] 接口契约不确定
- [ ] 不确定"改 A 会不会炸 B"

## 下游命令

- 审计通过 → `/tdd` (写测试)
- 发现冲突 → 修复后重新审计
