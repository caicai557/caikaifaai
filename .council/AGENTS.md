# Agent Council SOP (Lean v3 最终版)

> 靠制度自动做对，不靠记忆

## 模型路由（成本优先）

| 场景 | 模型 | 触发条件 |
|------|------|----------|
| 设计/架构/PRD | **Claude Opus 4.5** | 里程碑决策、异常契约 |
| 全库审计 | **Gemini 3 Pro** | ≥3 模块、超长上下文 |
| 高频实现 | **Gemini 3 Flash** | 默认：TDD、补测试、改配置 |
| 收尾审查 | **Codex** | commit/PR 前必过 |

## Token 成本对比

| 模型 | 输入 $/1M | 输出 $/1M | 用途 |
|------|:---------:|:---------:|------|
| Claude Opus 4.5 | 5 | 25 | 关键决策 |
| Gemini 3 Flash | 0.50 | 3.00 | 高频默认 |
| Gemini 3 Pro | 1~2 | 6~9 | 长上下文审计 |
| Codex | 1.25 | 10.00 | 审查验收 |

## 6 步 SOP（固定制度）

```text
1. Plan   (Opus)    → PRD/任务树/验收标准
2. TDD    (/tdd)    → 先写失败测试
3. Impl   (Flash)   → 最小改动，测试转绿
4. Verify (脚本)    → 一键门禁
5. Review (Codex)   → diff 挑刺审查
6. Ship   (/impl)   → commit + notes
```

## 命令速查

```bash
# 上下文治理
just codemap          # 生成 CODEMAP.md

# 规划
just plan "任务"      # Codex → SPEC.md
just audit            # Gemini → AUDIT.md

# 执行
/tdd <scope>          # TDD 门禁
/impl <scope>         # 实现
/verify               # 验收

# 验证
just verify           # 唯一门禁
```

## 门禁规则

1. ✅ `just verify` 必须通过
2. ✅ 契约测试必须存在
3. ✅ 接口变更 → DECISIONS.md
4. ✅ Review 通过才能 Ship

## Safety

- ❌ rm -rf, chmod -R
- ❌ .env, *.pem
- ✅ /sandbox 执行不可信脚本
- ✅ Git 可回滚
