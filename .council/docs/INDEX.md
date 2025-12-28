# AI Council 开发资料中心

> 自动生成于 2025-12-27 23:42:40

## 📚 文档导航

### 🎯 核心架构

| 文档 | 说明 | 状态 |
|------|------|------|
| [AGENTS.md](../AGENTS.md) | Agent 治理宪法 | ✅ |
| [CODEMAP.md](../../CODEMAP.md) | 项目代码地图 | ✅ |
| [SOP.md](../SOP.md) | 六步自愈循环 SOP | ✅ |
| [DECISIONS.md](../DECISIONS.md) | 架构决策日志 | ✅ |

### 🔧 最佳实践

| 文档 | 说明 |
|------|------|
| [TOKEN_SAVING_PRACTICES.md](../TOKEN_SAVING_PRACTICES.md) | Token 优化 |
| [MCP_PHILOSOPHY.md](../MCP_PHILOSOPHY.md) | MCP 协议理念 |
| [MCP_BEST_PRACTICES.md](../MCP_BEST_PRACTICES.md) | MCP 实操指南 |

### 🤖 模型专用指南

| 文档 | 目标模型 |
|------|----------|
| [CLAUDE.md](../CLAUDE.md) | Claude Opus 4.5 |
| [CODEX.md](../CODEX.md) | Codex 5.2 |
| [GEMINI.md](../GEMINI.md) | Gemini Pro/Flash |

## 🚀 快速开始

```bash
# 验证门禁
just verify

# 六步流程
/plan "需求"    # 1. PM 规划
/audit "模块"   # 2. 架构审计
/tdd "范围"     # 3. TDD
/impl "范围"    # 4. 实现
just verify      # 5. 裁决
/review          # 6. 审查
```

## 🎯 模型路由策略

| 模型 | 占比 | 场景 |
|------|------|------|
| Claude Opus 4.5 | 5% | 规划总控 |
| Codex 5.2 | 10% | 代码审查 |
| Gemini 3 Pro | 5% | 架构审计 |
| Gemini 3 Flash | 80% | 快速实现 |

---

**最后更新**: 2025-12-27 23:42:40
