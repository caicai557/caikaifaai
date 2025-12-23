# Agent Council SOP (Lean v2 可执行版)

> 针对 Claude Token 不足优化，Gemini 3 Flash 承担快速实现

## 角色分配 (Token 优化)

| Step | 角色 | 模型 | 动作 |
|:----:|------|------|------|
| 0 | - | 手动 | BRIEF + CODEMAP |
| 1 | Orchestrator | **Codex** | PRD → SPEC.md |
| 2 | Auditor | Gemini Pro | 按条件触发 → AUDIT.md |
| 3 | QA | **Gemini Flash** | TDD → 测试文件 |
| 4 | Executor | **Gemini Flash** | 实现 + verify |
| 5 | Gate | `just verify` | 三条硬门禁 |
| 6 | - | Gemini | NOTES + /clear |

## Step 0｜上下文治理 (30-90秒)

```bash
# 更新 BRIEF
vim .council/BRIEF.md  # Goal/Constraints/Acceptance/Verify

# 生成 CODEMAP
just codemap
```

**门禁**: BRIEF 必须有可测试验收标准 + `just verify`

## Step 1｜需求代码化 (Codex)

**输入**: BRIEF + CODEMAP + 任务一句话
**输出**: `SPEC.md`

```markdown
SPEC 必须包含:
- 任务树（小步）
- 文件清单
- 验收标准
- 验证命令: just verify
- 风险点 ≤5条
```

## Step 2｜全库审计 (Gemini Pro，按条件触发)

**触发条件** (满足任一):

- [ ] 影响 ≥3 模块
- [ ] 接口契约不确定
- [ ] 不确定"改 A 会不会炸 B"

**输出**: `AUDIT.md`

## Step 3｜TDD (Gemini Flash)

**输入**: SPEC.md (+ AUDIT.md)
**输出**: 测试文件

**门禁**:

- 新逻辑必须有新测试
- 不强求 90% 覆盖率（项目稳定后再加）

## Step 4｜实现 (Gemini Flash)

**输入**: 已存在的测试
**输出**: 最小 patch + NOTES 更新

**门禁**: `just verify` 全绿

## Step 5｜三条硬门禁 (替代 Wald)

1. ✅ `just verify` 必须通过
2. ✅ 契约测试必须存在且通过
3. ✅ 触及契约/接口 → DECISIONS.md 留条目

## Step 6｜收尾

- `/rewind` 回滚（如需）
- 更新 `NOTES.md`
- `/clear` 清理上下文

## 终极调优 (按需启用)

| 工具 | 启用条件 |
|------|----------|
| Docker 沙箱 | 不可信脚本/复杂依赖 |
| Git Worktree | 同时 2 条线 |
| MCP | 需要统一工具入口 |

## Safety

- ❌ rm -rf, chmod -R
- ❌ .env, *.pem
- ✅ Docker 沙箱
- ✅ Git 可回滚
