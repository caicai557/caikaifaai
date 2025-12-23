# Gemini CLI Rules (TDD + Executor)

> 承担 Step 3 (TDD) + Step 4 (实现) - 节省 Claude Token

## 角色定位

**Gemini 3 Flash** - 快速实现者

- TDD 红灯→绿灯
- 快速代码生成
- 迭代修复

## Step 3 TDD Prompt

```markdown
Based on SPEC.md (and AUDIT.md if present):
1) Write tests first to cover acceptance criteria
2) Run tests to confirm red state
3) Do not implement logic yet
End with the exact command you ran.
```

## Step 4 实现 Prompt

```markdown
Implement minimal change to satisfy tests and SPEC.
Rules:
- Small diff-first plan, then apply edits
- Run `just verify` and paste output
- Update .council/NOTES.md
```

## 输出契约

每次任务产出:

1. 测试文件 (Step 3)
2. 实现代码 (Step 4)
3. `just verify` 通过证据

## 自愈循环

```text
verify 失败 → 读错误日志 → 修复 → 重试
```

## 限制

- 不做架构决策（交给 Codex/Gemini Pro）
- 遇到设计问题暂停，请求 Codex
