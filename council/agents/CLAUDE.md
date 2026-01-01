# CLAUDE.md - Agents 模块规范

> 📍 **模块层**: `council/agents/`
> 🔗 **继承**: 项目根目录 `./CLAUDE.md` 规范

---

## 📌 模块职责

本目录包含所有专业化 Agent 实现，每个 Agent 有独立的系统提示词和模型配置。

---

## 🎭 Agent 清单

| Agent | 文件 | 角色 | 模型 |
|-------|------|------|------|
| Orchestrator | `orchestrator.py` | 任务拆解 | Claude Opus |
| Architect | `architect.py` | 架构设计 | Claude Opus |
| Coder | `coder.py` | 代码实现 | Gemini Flash |
| SecurityAuditor | `security_auditor.py` | 怀疑论者 | Codex |
| WebSurfer | `web_surfer.py` | 联网搜索 | Gemini Pro |

---

## 📋 模块特定规范 (NON-NEGOTIABLE)

> **YOU MUST** 遵守以下规范：

1. **继承 BaseAgent** - 所有 Agent 必须继承 `base_agent.py` 的 `BaseAgent`
2. **系统提示词** - 每个 Agent 必须定义 `*_SYSTEM_PROMPT` 常量
3. **类型注解** - 所有方法必须有完整类型注解
4. **硬化提示词** - SecurityAuditor 必须使用 XML 结构化标签

---

## 🛡️ SecurityAuditor 特殊规则

> **CRITICAL**: SecurityAuditor 是"极端怀疑论者"

- 绩效由发现的漏洞数量衡量
- 永不给代码"疑点利益"
- 如有疑问，返回 REJECT
- 目标 F1-Score >= 0.99

---

## 🔧 测试要求

```bash
# 运行 Agent 测试
pytest tests/test_real_agents.py -v

# 验证 Agent 导入
python -c "from council.agents import *"
```

---

## 🚫 禁止行为

- ❌ 直接在 Agent 中硬编码 API Key
- ❌ 跳过 BaseAgent 继承
- ❌ 使用默认模型而非专用模型

---

**最后更新**: 2026-01-01
