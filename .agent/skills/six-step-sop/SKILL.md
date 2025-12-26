---
name: six-step-sop
description: Complete 6-step self-healing development loop per .council/AGENTS.md. Use for any feature implementation from start to finish.
allowed-tools:
  - Bash
  - Edit
  - Read
  - Write
  - Task
---

## Six-Step SOP Instructions

> 遵循 `.council/AGENTS.md` 的标准操作程序

### Step 1: 开分支

```bash
git checkout -b feat/<feature-name>
```

- 分支名清晰
- 范围小于 1 小时工作量

### Step 2: 写验收标准

Update `.council/BRIEF.md`:

```markdown
## Goal
- **当前任务**: <一句话描述>

## Acceptance Criteria
- [ ] <可测试条件 1>
- [ ] <可测试条件 2>
```

### Step 3: Plan (Claude/Codex)

生成 `SPEC.md`:

1. 问题陈述 + 非目标
2. 任务树（小步骤）
3. 验收标准
4. 验证命令
5. 风险点

### Step 4: TDD 实现 (Gemini Flash)

```
1. 先写失败测试
2. 最小实现
3. 测试转绿
```

### Step 5: 裁决

```bash
just verify
```

- ✅ 通过 → 继续
- ❌ 失败 → 自愈循环（读错误 → 修复 → 重试）

### Step 6: 提交 + NOTES

```bash
# Update notes
echo "## $(date +%Y-%m-%d)" >> .council/NOTES.md

# Commit
git add -A
git commit -m "feat(<scope>): <description>"
```

## Model Routing

| 阶段 | 模型 | 触发条件 |
|------|------|----------|
| Plan | Claude Opus / Codex | 里程碑决策 |
| Impl | Gemini Flash | 默认实现 |
| Review | Codex | commit 前 |

## Example Usage

**Trigger phrases:**

- "Implement feature X following SOP"
- "Start 6-step workflow for X"
- "/six-step-loop"

**Expected output:**

- Branch created
- BRIEF updated
- SPEC generated
- Tests + implementation
- verify passed
- Commit ready
