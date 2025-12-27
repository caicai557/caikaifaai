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

| 场景 | 模型 | 触发条件 | 占比 | 上下文窗口 |
| :--- | :--- | :--- | :--- | :--- |
| **高难度/关键事项** | **Claude Opus 4.5** | 最重要事项、高风险决策、难题攻坚、长程推理 | 5% | 200k |
| **修复/对齐** | **Codex 5.2** | 代码审查、漏洞发现、大规模重构、边界对齐 | 10% | - |
| **超长上下文审计** | **Gemini 2.5 Pro** | 全库扫描、≥3模块审计、大规模代码阅读、查询资料实例 | - | **2M** |
| **深度推理审计** | **Gemini 3 Pro** | 复杂架构分析、多模态理解、工具使用、项目全面理解 | 5% | 1M |
| **前端开发** | **Gemini 3 Pro** | UI/UX 设计、组件开发、多模态还原 | ↑ | 1M |
| **快速实现** | **Gemini 3 Flash** | TDD、补测试、日常开发、迭代修复、快速代码 | 80% | 1M |

**模型选择指南**:
- **2M 超长上下文需求** → Gemini 2.5 Pro（可阅读 1,500 页文档、50,000 行代码、200+ 播客转录）
- **1M 高级推理 + 长上下文** → Gemini 3 Pro（推理能力最强，64k 输出，工具使用优秀）
- **日常高频开发** → Gemini 3 Flash（速度快，成本低，1M tokens）

## 3. 令牌经济学 (Tokenomics) - 2025 Optimized

| 模型 | 输入 $/1M | 输出 $/1M | 上下文窗口 | 适用场景 | 占比 |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Claude Opus 4.5** | $5.00 | $25.00 | 200k | 高难度/关键事项 | 5% |
| **Codex 5.2** | $1.25 | $10.00 | - | 审查/修复 | 10% |
| **Gemini 2.5 Pro** | $1.25 (≤200k)<br>$2.50 (>200k) | $10 (≤200k)<br>$15 (>200k) | **2M** | 超长上下文全库审计 | - |
| **Gemini 3 Pro** | $2.00 (≤200k)<br>$4.00 (>200k) | $12 (≤200k)<br>$18 (>200k) | 1M | 深度推理审计/前端 | 5% |
| **Gemini 3 Flash** | $0.50 | $3.00 | 1M | 快速代码实现 | 80% |

**成本优化建议**:
- **2M 超长上下文** → Gemini 2.5 Pro（性价比最高，>200k 时仅 $2.50 输入）
- **1M 深度推理** → Gemini 3 Pro（推理能力强，工具使用优秀）
- **日常高频任务** → Gemini 3 Flash（$0.50 输入，速度快）

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

### 4.6 Token 优化最佳实践

> **目标**: Session 保持在 50k tokens 以下（200k 预算的 25%），为复杂任务预留空间。

#### 🔴 禁止事项（高消耗）

1. **多次 Web 搜索**
   - ❌ 错误：分 3 次搜索 "Gemini 2.0", "Gemini 3.0", "pricing"
   - ✅ 正确：1 次综合搜索 "Gemini 2.0 2.5 3.0 Pro Flash context pricing 2025"

2. **重复写长报告**
   - ❌ 错误：写完整审查报告 → 发现错误 → 再写一遍
   - ✅ 正确：直接输出修正后的关键发现，引用原报告位置

3. **逐个处理批量任务**
   - ❌ 错误：用 Edit 工具逐个修改 9 个命令文件
   - ✅ 正确：写 Python 脚本批量处理（符合 4.3 代码模式）

#### 🟢 推荐做法

1. **信息查询**
   ```bash
   # 优先级：精准文档 > 综合搜索 > 多次搜索
   mcp__context7__get-library-docs  # 第一选择
   WebSearch("综合关键词 2025")      # 第二选择（仅 1 次）
   ```

2. **批量文件操作**
   ```python
   # 必须使用脚本，禁止循环调用 Edit
   import glob, re
   for f in glob.glob(".claude/commands/*.md"):
       content = open(f).read()
       content = re.sub(r'pattern', 'replacement', content)
       open(f, 'w').write(content)
   ```

3. **审查报告精简化**
   ```markdown
   # ❌ 详细版（20k tokens）
   ## 代码审查报告
   ### 审查范围...
   ### 初始错误...
   ### 修正过程...
   ### 教训总结...

   # ✅ 精简版（5k tokens）
   ## 审查发现
   - [P2] file:line - 问题描述 + 修复建议
   - 总体评价：⚠️ 条件通过
   ```

4. **读取文件时限制行数**
   ```python
   Read(file, limit=30)      # ✅ 仅读取关键部分
   Read(file)                # ❌ 读取全文（可能数千行）
   ```

#### 📊 Token 预算分配（200k Session）

| 阶段 | 预算 | 说明 |
|------|------|------|
| 需求理解 | 10k | 读取 SPEC, BRIEF, CODEMAP |
| 信息查询 | 15k | Web 搜索或文档查询（≤2 次） |
| 代码实现 | 20k | 写代码 + 测试 |
| 审查修复 | 10k | Codex 审查 + 修复 |
| 文档更新 | 5k | NOTES.md 记录 |
| **预留** | **140k** | 应对复杂情况和迭代 |

#### ⚠️ 超预算警告

当 Session tokens > 100k 时：
1. 停止当前任务
2. 输出已完成内容摘要
3. 建议用户开新 Session 继续

### 4.7 编排与决策层 (Orchestration & Decision)

> **理事会的"大脑"**: 顶层规划、任务分发、共识判定。

#### 🎯 主控编排者

**Codex 5.2 (o1/GPT-5.2)** - Orchestrator
- 高层需求拆解（PRD → 子任务树）
- 任务分发（根据模型路由表 2.0 分配）
- 进度监控与调度

#### 📒 双账本机制

| 账本类型 | 职责 | 存储位置 | 示例 |
|---------|------|---------|------|
| **任务账本** (Task Ledger) | 维护目标与子任务树 | `.council/BRIEF.md`<br>`.council/SPEC.md` | 任务 ID、依赖关系、验收标准 |
| **进度账本** (Progress Ledger) | 实时追踪执行状态 | `.council/NOTES.md` | 完成状态、耗时、风险点 |

**更新规则**:
- 每次 `/checkpoint` 后更新进度账本
- 任务拆解后立即写入任务账本
- 保持单一事实来源（SSOT）

#### 🎲 共识算法 (Wald Sequential Analysis)

**目标**: 动态决定"提交 / 继续 / 终止"

**决策公式**:
```
后验概率 π = P(任务成功 | 当前证据)
置信上限 α = 0.95  (95% 置信度)
风险下限 β = 0.05  (5% 容错率)

if π ≥ α:
    → 达成共识，提交 (git commit)
elif π ≤ β:
    → 终止任务，请求人工干预
else:
    → 继续迭代 (运行测试、收集证据)
```

**实现方式**:
```bash
# just verify 作为证据收集点
# 每次 verify 通过 → π 增加
# 每次 verify 失败 → 收集失败原因，修复后重试

# 示例：TDD 循环
π_0 = 0.5  # 初始概率
for iteration in range(max_iterations=5):
    run "just verify"
    if all_tests_pass:
        π += 0.2  # 证据累积
        if π ≥ 0.95:
            return "COMMIT"
    else:
        fix_failures()
        π += 0.1  # 部分进展

    if iteration == 4 and π < 0.95:
        return "MANUAL_INTERVENTION"
```

**触发时机**:
- `/verify` 通过后计算 π
- `/review` 发现高风险时降低 π
- 超过 3 次失败自动触发人工干预

#### 📊 决策流程图

```
需求输入 → Codex 编排 → 任务账本
    ↓
  分发任务 → 执行者 (Gemini/Claude)
    ↓
  verify → 更新 π → 判断
    ↓              ↓
  π≥α?         π≤β?
    ↓Yes          ↓Yes
  COMMIT       STOP
    ↓No
  继续迭代
```

### 4.8 并行加速 (Parallel Execution with Git Worktrees)

> **物理隔离**: 不同模块在独立工作目录并发开发，零合并冲突。

#### 🌲 Git Worktrees 架构

```
cesi/                         # 主工作区 (main)
├── .git/
└── src/

../cesi.worktrees/            # Worktrees 根目录
├── swarm/feature-auth/       # 任务 1: 用户认证
│   ├── .git -> ../../cesi/.git/worktrees/swarm-feature-auth
│   └── src/auth/
├── swarm/feature-payment/    # 任务 2: 支付模块
│   └── src/payment/
└── swarm/bugfix-login/       # 任务 3: 登录修复
    └── src/login/
```

**优势**:
- ✅ 物理隔离（不同目录 = 零文件冲突）
- ✅ 并发会话（3 个智能体同时工作）
- ✅ 独立分支（每个任务独立 branch）
- ✅ 快速切换（无需 git stash）

#### 🚀 并发执行流程

**启动并发任务**:
```bash
# 任务 1: 用户认证（Gemini 3 Flash）
just dev "实现 JWT 认证" &
worktree: swarm/feature-auth

# 任务 2: 支付模块（Gemini 3 Pro）
just dev "集成 Stripe 支付" &
worktree: swarm/feature-payment

# 任务 3: Bug 修复（Codex 5.2）
just dev "修复登录超时" &
worktree: swarm/bugfix-login

# 等待所有任务完成
wait
```

**工作区管理**:
```bash
# 创建工作区
./scripts/worktree_manager.sh create swarm/task-name

# 同步主工作区脚本
python3 scripts/dispatch_swarm.py --sync

# 清理已合并工作区
./scripts/worktree_manager.sh cleanup
```

#### 📋 任务分发策略

| 任务类型 | 模型 | Worktree 分支 | 预估时间 |
|---------|------|--------------|---------|
| **新功能** | Gemini 3 Flash | `swarm/feature-*` | 30-60 分钟 |
| **架构审计** | Gemini 2.5 Pro | `swarm/audit-*` | 15-30 分钟 |
| **Bug 修复** | Codex 5.2 | `swarm/bugfix-*` | 10-20 分钟 |
| **代码审查** | Codex 5.2 | `swarm/review-*` | 5-10 分钟 |

**并发度控制**:
- 最大并发数 = `CPU 核心数 / 2`（避免资源竞争）
- 推荐：3-4 个并发任务
- 超过 5 个任务建议排队

#### ⚠️ 注意事项

1. **避免同时修改相同文件**
   - 任务拆解时确保模块独立
   - 共享文件（如 `pyproject.toml`）由主工作区统一修改

2. **定期同步主分支**
   ```bash
   # 在每个 worktree 中
   git fetch origin main
   git rebase origin/main
   ```

3. **清理临时工作区**
   ```bash
   # 合并后立即清理
   git worktree remove ../cesi.worktrees/swarm/feature-auth
   git branch -d swarm/feature-auth
   ```

#### 🔄 集成到工作流

```bash
# 方式 1: 手动并发（开发者控制）
just dev "任务 1" &
just dev "任务 2" &
wait && just ship

# 方式 2: 自动并发（dispatch_swarm.py）
python3 scripts/dispatch_swarm.py \
  --task "feature-auth" \
  --task "feature-payment" \
  --parallel

# 方式 3: 交互式选择（推荐）
./scripts/worktree_manager.sh interactive
```

**详细实现**: 参考 `scripts/worktree_manager.sh` 和 `scripts/dispatch_swarm.py`

### 4.9 通信协议 (MCP Integration)

> **模型上下文协议 (MCP)**: 实现工具"即插即用"，智能体动态发现并调用外部资源。

#### 🔌 核心理念

- **动态发现**: 无需硬编码，智能体自动发现可用工具
- **标准接口**: 统一协议访问 GitHub、Slack、数据库等
- **按需加载**: JIT (Just-In-Time) 原则，仅加载当前任务需要的工具

#### 📦 已集成 MCP 服务器

| 服务器 | 功能 | 使用场景 | 默认状态 |
|--------|------|----------|----------|
| **filesystem** | 文件读写、目录遍历 | 所有任务 | ✅ 默认启用 |
| **context7** | 获取最新库文档 | 查询 API 文档 | 🟡 按需启用 |
| **github** | PR/Issue 管理、代码搜索 | Git 工作流 | 🔴 用户配置 |
| **fetch** | 网页抓取、内容提取 | 信息查询 | 🔴 用户配置 |
| **codex** | 代码审查、会话管理 | 审查任务 | 🟡 CLI 模式 |

#### 🚀 使用示例

```python
# ✅ 正确：MCP 自动发现工具
# 智能体会自动调用 mcp__github__create_issue
"创建 Issue: 修复登录 bug"

# ✅ 正确：Context7 精准文档
mcp__context7__get-library-docs(
    context7CompatibleLibraryID="/mongodb/docs",
    topic="aggregation"
)

# ❌ 错误：手动实现已有 MCP 功能
subprocess.run(["gh", "issue", "create", ...])  # GitHub MCP 已提供
```

#### 📋 配置分层（参考 MCP_BEST_PRACTICES.md）

1. **项目级** (`.mcp.json`)
   - 仅保留必需工具（filesystem）
   - 轻量、快速启动

2. **用户级** (`~/.claude.json`)
   - 重型工具（GitHub、Database）
   - 需要 Token 的服务
   - 按需启用/禁用

#### ⚡ JIT 加载策略

```bash
# 需要 GitHub 功能时
1. 临时启用: 在 Claude Code settings 中启用 GitHub MCP
2. 执行任务: 创建 PR、审查代码
3. 立即禁用: 完成后禁用，释放上下文

# 避免全局启用重型 MCP（浪费 tokens）
```

#### 🛠️ 扩展新 MCP 服务器

```json
// config/mcp_user_config.template.json
{
  "mcpServers": {
    "postgres": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-postgres"],
      "env": {
        "DATABASE_URL": "postgresql://..."
      }
    }
  }
}
```

**详细指南**: 参考 `.council/MCP_BEST_PRACTICES.md`
