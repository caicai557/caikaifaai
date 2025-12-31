# Council - Multi-Model Agent Framework

## 快速开始 (Claude Code)

在 Claude Code 中使用以下命令：

```
/council-dev "实现用户登录功能"
/council-classify "重构数据库模块"
/council-route "删除用户数据"
/council-test
```

## 命令行使用

```bash
# 设置环境变量
export GEMINI_API_KEY="your-key"
export PYTHONPATH=/home/zz113/Desktop

# 运行开发任务
python -m council.cli dev "任务描述"

# 分类任务
python -m council.cli classify "任务描述"

# 路由决策
python -m council.cli route "任务描述"

# 运行测试
python -m pytest tests/ -v
```

## 架构

### Agents

| Agent | 职责 |
|-------|------|
| **Architect** | 宏观设计 |
| **Coder** | 代码实现 |
| **Reviewer** | 质量把控 |

### 状态机 (EPCC)

```
EXPLORING → ANALYZING → PLANNING → CODING → TESTING → HEALING → REVIEWING → COMPLETED
```

## 核心组件

- `dev_orchestrator.py` - 编排器
- `agents/` - 智能体
- `memory/` - 向量记忆
- `facilitator/wald_consensus.py` - Wald 共识
- `orchestration/adaptive_router.py` - 自适应路由

## 🌟 最佳实践工作流 (The Golden Workflow)

为了发挥 Council 的最大效能，建议遵循以下 **"人机协作环 (Human-in-the-Loop)"**：

### 1. 准备阶段 (Preparation)

- **定义规范**: 确保项目根目录有 `CLAUDE.md`，明确代码风格、测试规范和架构原则。Council 会自动读取并遵守。
- **环境自检**: 运行 `python -m council.cli check` (需实现) 或手动检查环境变量 `GEMINI_API_KEY`。

### 2. 任务分发 (Dispatch)

不要盲目丢任务，先分类：

- **简单修复**: 直接使用 Claude Code 原生能力。
- **复杂功能/重构**: 使用 `/council-dev`。
  - *Tip*: 描述任务时使用 **"CO-STAR"** 框架 (Context, Objective, Style, Tone, Audience, Response)。
  - *Example*: `/council-dev "Context: 用户反馈登录慢。Objective: 引入 Redis 缓存优化 token 验证。Style: 遵循现有装饰器模式。"`

### 3. 监控与干预 (Monitor & Intervene)

Council 运行时是自动化的，但你可以：

- **查看日志**: 观察 `dev_orchestrator.py` 的输出，了解当前处于 EPCC 的哪个阶段。
- **审查计划**: 在 `PLANNING` 阶段生成的计划，如果发现方向不对，及时终止并调整 Prompt。

### 4. 验收与自愈 (Review & Heal)

- **自愈循环**: Council 会自动运行测试。如果失败，它会尝试修复。
- **人工验收**: 当状态变为 `REVIEWING` 或 `COMPLETED` 时，**务必**进行人工 Code Review。不要盲目信任 AI 的代码。
- **查看成本**: 检查 TokenTracker 输出，评估本次开发的 ROI。

## 💡 高级技巧 (Pro Tips)

- **利用缓存**: Council 实现了 Prompt Caching。对于重复性任务（如"为所有文件添加类型注解"），第二次运行会快得多且便宜。
- **工具白名单**: 在 `.council/allowlist.json` (默认配置) 中严格限制文件操作范围，防止误删重要数据。
- **多模型策略**:
  - 需要深度思考的架构设计 -> 显式指定 `TaskType=PLANNING` (触发 GPT-5.2/Claude Opus)。
  - 大量简单的代码生成 -> 显式指定 `TaskType=CODING` (触发 Claude Sonnet/Gemini Flash)。
