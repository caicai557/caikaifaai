# Agent Council Governance (2025.12 六步自愈循环)

> **SSOT**: 多智能体协同开发标准操作程序

## 模型能力矩阵 (Token 优先分配)

| 模型 | 最强能力 | 角色 | Token 策略 |
|------|----------|------|:----------:|
| **Codex (GPT-5.2)** | 逻辑拆解/任务分发 | Orchestrator | 高密集 |
| **Gemini 3 Pro** | 2M 长上下文/全库审计 | Architect | 长文档 |
| **Claude 4.5 Opus** | 物理执行/写文件 | Executor | Code Mode 98.7% 节省 |
| **Gemini 3 Flash** | 快速代码生成 | TDD 实现 | 高频迭代 |

## 六步自愈循环 SOP

```text
┌─────────────────────────────────────────────────────────────────┐
│  1. PM      2. 架构师    3. QA      4. 执行    5. 裁决   6. 总结  │
│  Codex  →  Gemini Pro → Claude  →  Claude  → verify → Gemini   │
│  PRD        全库审计     TDD先行    Code Mode  自愈循环  NOTES    │
└─────────────────────────────────────────────────────────────────┘
```

### 阶段 1: 需求代码化 (PM)

- **主控**: Codex (GPT-5.2)
- **输入**: 模糊用户指令
- **输出**: 结构化 PRD + 任务树
- **产物**: `BRIEF.md` 更新

### 阶段 2: 全库审计与设计 (架构师)

- **主控**: Gemini 3 Pro (2M tokens)
- **动作**: 扫描整个代码库，发现冲突
- **输出**: 技术设计文档
- **产物**: `implementation_plan.md`

### 阶段 3: TDD 强制约束 (QA)

- **主控**: Claude Code
- **规则**: 测试覆盖率 < 90% 禁止进入执行
- **输出**: 测试用例
- **产物**: `tests/test_*.py`

### 阶段 4: 程序化并行执行 (执行官)

- **主控**: Claude Code (Code Mode)
- **核心技巧**: 编写 Python 脚本批量执行
- **Token 节省**: 约 98.7%
- **输出**: 实现代码

### 阶段 5: 自愈校验 (裁决)

- **动作**: `just verify`
- **失败处理**: 自愈循环 (错误日志 → 修复 → 重试)
- **共识算法**: Wald 序列分析
- **规则**: 分歧过大 → 人在回路审计

### 阶段 6: 总结与回滚 (收尾)

- **主控**: Gemini
- **动作**:
  1. `/rewind` 建立快照
  2. 更新 `NOTES.md`
  3. `/clear` 重置会话

## 资源分担策略 (Token 优先)

| 角色 | 模型 | 负责 | Token 消耗 |
|------|------|------|:----------:|
| **PM** | Codex | 逻辑拆解、任务分发 | 高 |
| **审计** | Gemini Pro | 长文档、跨文件、历史回溯 | 高 |
| **执行** | Claude Code | 写文件、跑命令、Git 提交 | 低 (Code Mode) |

## 工程化配置

### 环境隔离

```bash
# Docker 沙箱 (强制)
docker run --rm -v $(pwd):/workspace -w /workspace python:3.12 pytest
```

### 并行加速 (Git Worktrees)

```bash
git worktree add ../project-feature-a feature-a
git worktree add ../project-bugfix bugfix-123
# 不同 Claude 会话在不同工作树并行
```

### MCP 协议

统一接口挂载:

- GitHub
- 数据库
- Slack

## Hard Safety Boundaries

- ❌ rm -rf, format disk, chmod -R
- ❌ 读取 .env, *.pem, credentials
- ✅ Docker 沙箱执行
- ✅ Git 可回滚

## Definition of Done

- [ ] Tests pass (coverage ≥ 90%)
- [ ] `just verify` pass
- [ ] NOTES updated
- [ ] Snapshot created
