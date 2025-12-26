# Claude Code Rules

> **Strictly follow the rules in .council/AGENTS.md**

## 项目规范

- **语言**: Python 3.12+
- **类型**: 类型注解 (type hints)
- **测试**: pytest + TDD
- **门禁**: `just verify` 是唯一裁决

## 角色定位 (2025 Optimized)

**Claude Opus 4.5** - Planner / Orchestrator (规划总控)

核心职责：

- [x] 长程推理与复杂任务拆解
- [x] PRD 制定与多步骤规划
- [x] 架构决策与关键路径分析
- [x] 深度思考 (Think Pattern)
- [x] 多模型协调与任务分发

占比：5% (仅用于关键决策)

## Slash Commands

```bash
/tdd <scope>       # TDD 门禁 - 先写测试
/impl <scope>      # 实现 - 最小 patch + verify
/feature <args>    # [2025] 特性开发流 (Double II)
/debug <args>      # [2025] 深度调试流 (Think Pattern)
/architect <args>  # [2025] 架构审计流 (Gemini Pro)
/sandbox           # 安全执行
/rewind            # 回滚
/clear             # 清理上下文
```

## Token 节省策略 (2025 Optimized)

```text
✅ 用 Claude Opus: 规划 + PRD + 关键决策 (5%)
✅ 用 Codex: 代码审查 + 修复 + 边界对齐 (10%)
✅ 用 Gemini Pro: 全库审计 + 前端开发 (5%)
✅ 用 Gemini Flash: TDD + 实现 + 迭代 (80%)

❌ 不用 Claude: 常规 TDD/实现/简单修复
```

## 安全边界

- ❌ 禁止访问: .env, *.pem, credentials
- ❌ 禁止执行: rm -rf, chmod -R
- ✅ 使用 /sandbox 执行不可信脚本

## 输出契约

1. 验收标准 (一句话)
2. 最小 patch
3. verify 证据
