# CLAUDE.md - Council 项目规范

> **⚠️ IMPORTANT: Strictly follow the rules in ./AGENTS.md**
> **🏛️ 宪法联动: 本文档与 AGENTS.md 权限矩阵深度绑定**

---

## 📊 分层治理架构

本项目采用三层CLAUDE.md分层加载策略：

| 层级 | 路径 | 职责 |
|------|------|------|
| **全局层** | `~/.claude/CLAUDE.md` | 个人偏好、通用设置 |
| **项目层** | `./CLAUDE.md` (本文件) | 核心规范、构建命令 |
| **模块层** | `./council/*/CLAUDE.md` | 模块细粒度指令 |

---

## 📌 项目概述

**Council** 是一个多智能体协作系统，采用 Hub-and-Spoke + A2A Mesh 架构。

## 🛠️ 技术栈

| 组件 | 技术 |
|------|------|
| **语言** | Python 3.12+ |
| **类型** | Pydantic v2 |
| **异步** | asyncio |
| **测试** | pytest + pytest-asyncio |
| **Lint** | ruff |
| **格式** | black |

## 📁 项目结构

```
council/
├── agents/          # Agent 实现
├── auth/            # RBAC 权限系统
├── governance/      # 治理网关
├── facilitator/     # Wald 共识引擎
├── orchestration/   # 编排模块 (三权分立)
├── self_healing/    # 自愈循环
├── tools/           # PTC 工具
├── skills/          # 技能模块
├── workflow/        # 六步工作流
└── sandbox/         # Docker 沙盒
```

---

## 🏛️ 三权分立模型配置

| 角色 | Agent | 模型 | 用途 |
|------|-------|------|------|
| **Orchestrator** | 规划者 | `codex-5.2` | 逻辑拆解 |
| **Oracle** | 审计者 | `gemini-3-pro` | 200万Token全库扫描 |
| **Executor** | 执行者 | `claude-4.5-sonnet` | 精准执行 (≤500行) |
| **FastCoder** | 快速编码 | `gemini-3-flash` | 大量代码 (80%) |
| **SecurityAuditor** | 怀疑论者 | `codex-5.2` | 安全审计 |

> ⚠️ **IMPORTANT: 大范围扫描或长上下文 YOU MUST 使用 Gemini**

---

## 🔧 构建命令 (唯一裁决)

```bash
# ⚠️ YOU MUST 运行验证门禁
just verify          # compile + lint + test

# 运行测试
pytest tests/ -v

# Lint 检查
ruff check .

# 格式化
ruff format .

# CLI 命令
council init          # 生成 CLAUDE.md
council codemap       # 生成代码地图
council tripartite    # 三权分立执行
```

---

## 📋 强制代码规范 (NON-NEGOTIABLE)

> **YOU MUST** 遵守以下规范，无例外：

1. **类型注解必须** - 所有函数必须有类型注解
2. **Small Diffs** - 每次改动 ≤200 行
3. **TDD 优先** - 先写测试，后写实现
4. **防御性编程** - 空值/异常/竞态必须处理
5. **Vitest/pytest** - 新功能必须附带测试

---

## 🔄 六步自愈循环

```
1. Plan    → Codex 需求代码化
2. Audit   → Gemini Pro 全库审计 (200万Token)
3. TDD     → Claude Sonnet 测试生成
4. Impl    → Gemini Flash 代码实现
5. Verify  → pytest/ruff 验证
6. Review  → Wald 共识裁决 (π ≥ 0.95 自动提交)
```

---

## 🚫 禁止行为 (CRITICAL - 违反将触发 REJECT)

> **YOU MUST NOT** 执行以下操作：

- ❌ 修改 `.env`, `secrets/`, `.ssh/` 等敏感路径
- ❌ 执行 `rm -rf`, `chmod -R 777` 等危险命令
- ❌ 在沙盒外执行 Agent 生成的代码
- ❌ 跳过测试直接提交
- ❌ 使用过时信息 (2024年及以前的资料需标记)

---

## 🔒 安全边界

```yaml
sensitive_paths:
  - .env*
  - secrets/
  - .ssh/
  - **/credentials*

dangerous_commands:
  - rm -rf
  - chmod -R
  - dd if=
  - mkfs.*
```

---

## 🤝 Git 协作流程 (Conventional Commits)

> **YOU MUST** 遵循以下规范：

### 分支命名

```
feat/<描述>      # 新功能
fix/<描述>       # Bug修复
docs/<描述>      # 文档更新
refactor/<描述>  # 重构
test/<描述>      # 测试
```

### Commit 消息格式

```
<type>(<scope>): <description>

[可选 body]

[可选 footer]
```

**类型 (type):**
- `feat`: 新功能
- `fix`: Bug修复
- `docs`: 文档
- `refactor`: 重构
- `test`: 测试
- `chore`: 构建/工具

**示例:**
```
feat(agents): 添加SecurityAuditor硬化提示词
fix(wald): 修复早停Token计算
docs(claude): 更新分层治理架构
```

### 合并策略

- ✅ **Squash Merge** - 默认策略
- ✅ **Rebase** - 保持线性历史
- ❌ **Merge Commit** - 仅用于重要里程碑

---

## 📝 动态增量更新

开发过程中使用 `#` 键记录决策到本文件：
- 新发现的最佳实践
- 项目特定约定
- 模型调优参数

---

## 📊 四大核心用途检查

| 用途 | 覆盖 | 位置 |
|------|------|------|
| 工程标准与风格指南 | ✅ | 强制代码规范 |
| 核心命令与自动化脚本 | ✅ | 构建命令 |
| 项目架构与目录索引 | ✅ | 项目结构 |
| Git协作流程 | ✅ | 本节 |

---

**最后更新**: 2026-01-01
**版本**: 2.1 (四大核心用途完备)
