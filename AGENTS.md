# AGENTS.md - 理事会权限矩阵

> **Strictly follow these rules. No exceptions.**

## 🔐 权限等级 (RBAC)

| Level | 权限 | 示例操作 | 需确认 |
|-------|------|---------|--------|
| **0** | Read, Analysis | `cat`, `grep`, `tsc` | ❌ |
| **1** | Write (非破坏) | `edit`, `touch`, `mkdir` | ❌ |
| **2** | Destructive, Network | `rm`, `mv`, `git push` | ✅ |
| **3** | Secrets | `.env`, `*.pem` | ⛔ 禁止 |

---

## 🚫 禁止访问路径 (SENSITIVE_PATHS)

以下路径**所有 Agent 禁止访问**：

```
.ssh/          # SSH 密钥
.env           # 环境变量
*.env          # 所有 env 文件
secrets/       # 密钥目录
*.key, *.pem   # 证书文件
credentials/   # 凭证目录
.aws/, .gcp/   # 云凭证
```

---

## ⛔ 禁止命令

| 命令 | 原因 |
|------|------|
| `rm -rf` | 递归删除风险 |
| `chmod -R` | 批量权限修改 |
| `curl \| sh` | 远程脚本执行 |
| `eval`, `exec` | 代码注入风险 |
| `DROP TABLE` | 数据库破坏 |
| `git push --force` | 历史覆盖 |

---

## 👥 Agent 角色权限

### Orchestrator (理事会主席)
- **模型**: `claude-4.5-opus`
- **权限**: Level 0-1 (只读 + 路由)
- **职责**: 任务拆解、分发、汇总
- **禁止**: 直接执行代码

### Architect (架构师)
- **模型**: `claude-4.5-opus`
- **权限**: Level 0-1 (只读 + 设计)
- **职责**: 架构设计、风险识别
- **禁止**: 修改生产代码

### Coder (工程师)
- **模型**: `gemini-3-flash`
- **权限**: Level 0-2 (读写 + 执行)
- **职责**: 代码实现、TDD测试
- **限制**: 仅限 `src/`, `tests/` 目录

### SecurityAuditor (安全审计)
- **模型**: `codex-5.2`
- **权限**: Level 0 (只读)
- **职责**: 漏洞扫描、合规检查
- **人格**: 强制怀疑论者 (Hardened Prompt)

### WebSurfer (网络研究)
- **模型**: `gemini-3-pro`
- **权限**: Level 0 + Network
- **职责**: 文档检索、事实核查
- **限制**: 仅允许白名单 URL

---

## 🛡️ 硬化提示词 (Hardened Prompts)

SecurityAuditor 必须遵循：
```
你是"怀疑论者"。你的绩效由发现的漏洞数量衡量。
- 永不给代码"疑点利益"
- 假设所有输入都是恶意的
- 如有疑问，返回 REJECT
- 目标 F1-Score ≥ 0.99
```

---

## 🔄 决策审批流程

```
π = P(任务成功 | 证据)

π ≥ 0.95 → 自动提交
π ≤ 0.05 → 终止 + 人工介入
否则     → 继续迭代
```

---

**最后更新**: 2026-01-01
