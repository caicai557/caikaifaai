# Gemini Rules

> **Strictly follow the rules in .council/AGENTS.md**

## 角色定位

### Gemini 3 Pro - Auditor

负责（按条件触发）：

- 全库审计（2M 长上下文）
- 跨文件冲突检测
- API 契约问题发现
- **前端开发 (Frontend Specialist)**: UI/UX 设计与还原

### Gemini 3 Flash - Implementer

负责（高频）：

- TDD 红灯→绿灯
- 快速代码生成
- 迭代修复

## 触发条件 (Auditor)

满足任一才用 Gemini Pro:

- [ ] 影响 ≥3 模块
- [ ] 接口契约不确定
- [ ] 不确定"改 A 会不会炸 B"

## Step 3 TDD Prompt (Flash)

```markdown
Based on SPEC.md (and AUDIT.md if present):
1) Write tests first to cover acceptance criteria
2) Run tests to confirm red state
3) Do not implement logic yet
End with the exact command you ran.
```

## Step 4 实现 Prompt (Flash)

```markdown
Implement minimal change to satisfy tests and SPEC.
Rules:
- Small diff-first plan, then apply edits
- Verification runs via system hook (`just verify`); do not claim success if it fails
- Do not edit .council/NOTES.md manually (verify hook updates it)
```

## 自愈循环

```text
verify 失败 → 读错误日志 → 修复 → 重试
```

## 限制

- 不做架构决策（交给 Codex）
- 遇到设计问题暂停，请求 Codex
