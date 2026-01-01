# CLAUDE.md - Council 项目规范

> **Strictly follow the rules in ./AGENTS.md**

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
├── facilitator.py   # Wald 共识引擎
├── orchestration/   # 编排模块
├── self_healing/    # 自愈循环
├── tools/           # PTC 工具
└── sandbox/         # 沙盒执行
```

## 🎯 模型配置

| Agent | 模型 | 用途 |
|-------|------|------|
| Orchestrator | `claude-4.5-opus` | 规划、分发 |
| Architect | `claude-4.5-opus` | 架构设计 |
| Coder | `gemini-3-flash` | 代码实现 (80%) |
| SecurityAuditor | `codex-5.2` | 安全审计 |
| WebSurfer | `gemini-3-pro` | 长上下文研究 |

> ⚠️ **大范围扫描或长上下文必须使用 Gemini**

## 🔧 构建命令

```bash
# 验证门禁 (唯一裁决)
just verify          # compile + lint + test

# 运行测试
pytest tests/ -v

# Lint 检查
ruff check .

# 格式化
ruff format .
```

## 📋 代码规范

1. **类型注解必须** - 所有函数必须有类型注解
2. **Small Diffs** - 每次改动 ≤200 行
3. **TDD 优先** - 先写测试，后写实现
4. **防御性编程** - 空值/异常/竞态必须处理

## 🔄 六步自愈循环

```
1. Plan    → Codex 需求代码化
2. Audit   → Gemini Pro 全库审计
3. TDD     → Claude Sonnet 测试生成
4. Impl    → Gemini Flash 代码实现
5. Verify  → pytest/ruff 验证
6. Review  → Wald 共识裁决
```

## 🚫 禁止行为

- 不修改 `.env`, `secrets/` 等敏感路径
- 不执行 `rm -rf`, `chmod -R` 等危险命令
- 不在沙盒外执行 Agent 生成的代码
- 不跳过测试直接提交

---

**最后更新**: 2026-01-01
