# Agent Council Constitution (AGENTS.md)

> **核心原则**: 上下文治理是防止认知漂移的唯一防线。

## 1. 权限矩阵 (RBAC)

| 操作 | 权限级别 | 需询问? | 备注 |
| :--- | :--- | :--- | :--- |
| **Read** (cat, ls, grep) | 🟢 **Level 0** | No | 允许自由探索 |
| **Analysis** (tsc, lint) | 🟢 **Level 0** | No | 允许无副作用检查 |
| **Write** (edit, touch) | 🟡 **Level 1** | No* | *仅限非破坏性修改 (TDD/Impl) |
| **Destructive** (rm, mv) | 🔴 **Level 2** | **YES** | 必须确认 Diff |
| **Network** (push, npm) | 🔴 **Level 2** | **YES** | 必须确认 |
| **Secrets** (.env, keys) | ⛔ **Level 3** | **STRICT** | 严禁触碰 |

## 2. 模型路由 (Model Routing) - 2025 Optimized

| 场景 | 模型 | 触发条件 | 占比 |
| :--- | :--- | :--- | :--- |
| **规划/管理** | **Claude Opus 4.5** | 长程推理、复杂任务拆解、PRD、多步骤规划 | 5% |
| **修复/对齐** | **Codex 5.2** | 代码审查、漏洞发现、大规模重构、边界对齐 | 10% |
| **前端开发** | **Gemini 3 Pro** | UI/UX 设计、组件开发、多模态还原 | 5% |
| **全库审计** | **Gemini 3 Pro** | ≥3 模块、2M 超长上下文扫描 | - |
| **高频实现** | **Gemini 3 Flash** | TDD、补测试、日常开发、迭代修复 | 80% |

## 3. 令牌经济学 (Tokenomics) - 2025 Optimized

| 模型 | 输入 $/1M | 输出 $/1M | 适用场景 | 占比 |
| :--- | :--- | :--- | :--- | :--- |
| Claude Opus 4.5 | $5.00 | $25.00 | 规划/PRD | 5% |
| Gemini 3 Pro | - | - | 审计/前端 | 5% |
| Gemini 3 Flash | $0.50 | $3.00 | TDD/实现 | 80% |
| Codex 5.2 | $1.25 | $10.00 | 审查/修复 | 10% |

## 4. 核心协议 (Protocols)

### 4.1 上下文治理

- **单一事实来源**: 所有规则以 `AGENTS.md` 和 `CLAUDE.md` 为准。
- **非损压缩**: 会话 Token > 80% 时，必须执行 `context_manager.py compact`。

### 4.2 渐进式披露

- **禁止**: 初始加载所有工具。
- **强制**: 使用 `tool_search` 按需加载工具。

### 4.3 代码模式 (PTC)

- **禁止**: 使用自然语言进行批量文件操作。
- **强制**: 编写 Python 脚本在沙盒中执行 (Batch Ops)。

### 4.4 双重架构 (Double II)

- **Information**: 规划阶段 (Plan) 必须与执行分离，使用 `--dry-run`。
- **Implementation**: 执行阶段 (Impl) 仅在规划确认后进行。

### 4.5 深度思考 (Think Pattern)

- **高风险操作**: 必须先输出 `<thinking>` 标签推演根因。
- **禁止**: 直接生成代码而不进行假设验证。
