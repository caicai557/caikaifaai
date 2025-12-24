# Claude Code Rules

> **Strictly follow the rules in .council/AGENTS.md**

## 项目规范

- **语言**: Python 3.12+
- **类型**: 类型注解 (type hints)
- **测试**: pytest + TDD
- **门禁**: `just verify` 是唯一裁决

## 角色定位

**Claude 4.5** - 备用执行者 (Token 节省模式)

仅在以下情况使用 Claude:

- [ ] Gemini Flash 无法处理的复杂逻辑
- [ ] 需要 /sandbox 执行不可信脚本
- [ ] 需要 /rewind 回滚

## Slash Commands

```bash
/tdd <scope>   # TDD 门禁 - 先写测试
/impl <scope>  # 实现 - 最小 patch + verify
/sandbox       # 安全执行
/rewind        # 回滚
/clear         # 清理上下文
```

## Token 节省策略

```text
✅ 用 Gemini Flash: TDD + 实现 + 迭代
✅ 用 Codex: PRD + 任务拆分
✅ 用 Gemini Pro: 全库审计

❌ 不用 Claude: 常规 TDD/实现
```

## 安全边界

- ❌ 禁止访问: .env, *.pem, credentials
- ❌ 禁止执行: rm -rf, chmod -R
- ✅ 使用 /sandbox 执行不可信脚本

## 输出契约

1. 验收标准 (一句话)
2. 最小 patch
3. verify 证据
