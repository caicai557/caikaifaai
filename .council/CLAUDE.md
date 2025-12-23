# Claude Code Rules (Token 节省模式)

> Claude Token 有限 - 仅在必要时使用

## 角色定位

**Claude 4.5** - 备用执行者

仅在以下情况使用 Claude:

- [ ] Gemini Flash 无法处理的复杂逻辑
- [ ] 需要 /sandbox 执行不可信脚本
- [ ] 需要 /rewind 回滚

## Token 节省策略

```text
✅ 用 Gemini Flash: TDD + 实现 + 迭代
✅ 用 Codex: PRD + 任务拆分
✅ 用 Gemini Pro: 全库审计

❌ 不用 Claude: 常规 TDD/实现
```

## 仅限命令

```bash
/sandbox  # 安全执行
/rewind   # 回滚
/clear    # 清理
```

## 输出契约

当使用 Claude 时:

1. 验收标准 (一句话)
2. 最小 patch
3. verify 证据
