# 代码地图 (Code Map)

> 本文档提供项目的整体结构视图，帮助 AI 智能体快速理解项目上下文。
> **最后更新**: 2025-12-29

## 项目概览

| 字段 | 值 |
|------|-----|
| **项目名称** | cesi-council |
| **项目类型** | Python 后端应用 |
| **主要用途** | 多智能体理事会框架 (AGI 开发工作流) |
| **Python 版本** | 3.12+ |
| **架构模式** | 层级监督 + Wald 共识 + PTC 程序化调用 |
| **代码行数** | ~12,200 行 |

## 目录结构

```
cesi-council/
├── src/                          # 应用源码
│   ├── config.py                 # 全局特性开关
│   ├── calculator.py             # 工具模块
│   └── seabox/                   # API 服务器模块
├── council/                      # 核心理事会模块 (68 files)
│   ├── agents/           (13)    # 智能体实现
│   ├── facilitator/      (4)     # 共识机制
│   ├── orchestration/    (10)    # 编排层 ⬆️
│   ├── governance/       (4)     # 治理层
│   ├── protocol/         (2)     # 通信协议
│   ├── context/          (4)     # 上下文管理 ⬆️
│   ├── memory/           (4)     # 长期记忆
│   ├── mcp/              (5)     # MCP 服务器
│   ├── self_healing/     (3)     # 自愈循环
│   ├── tdd/              (2)     # TDD 工具
│   ├── auth/             (2)     # 认证模块
│   ├── prompts/          (1)     # 提示词模板
│   └── tests/            (13)    # 模块测试
├── tests/                        # 主测试套件 (25 files)
├── scripts/                      # 工具脚本 (35 files)
├── config/                       # 配置文件
├── .council/                     # 多模型理事会配置
├── .claude/                      # Claude Code 配置
├── Justfile                      # 构建命令
└── pyproject.toml                # 项目元数据
```

## Council 核心模块

### 1. agents/ - 智能体层

| 类名 | 文件 | 职责 |
|------|------|------|
| `BaseAgent` | base_agent.py | 抽象基类，`_call_llm_structured()` |
| `Orchestrator` | orchestrator.py | 理事会主席，任务拆解 |
| `ArchitectAgent` | architect.py | 架构师智能体 |
| `CoderAgent` | coder.py | 工程师智能体 |
| `SecurityAuditor` | security_auditor.py | 安全审计 (一票否决) |

### 2. orchestration/ - 编排层

| 类名 | 文件 | 职责 |
|------|------|------|
| `TaskClassifier` | task_classifier.py | **多模型智能路由** |
| `AgentRegistry` | agent_registry.py | **动态 Agent 发现** |
| `DelegationManager` | delegation.py | **委托链管理** |
| `AdaptiveRouter` | adaptive_router.py | 风险分级路由 |
| `BlastRadiusAnalyzer` | blast_radius.py | 代码影响分析 |
| `Hub` | hub.py | Pub/Sub 消息总线 |
| `DualLedger` | ledger.py | 双账本 (Task/Progress) |
| `StateGraph` | graph.py | 状态机图 |

### 3. context/ - 上下文管理

| 类名 | 文件 | 职责 |
|------|------|------|
| `RollingContext` | rolling_context.py | 滑动窗口上下文 |
| `GeminiCacheManager` | gemini_cache.py | **Gemini 服务端缓存** |
| `AutoCompactTrigger` | auto_compact.py | **自动压缩触发器** |

### 4. governance/ - 治理层

| 类名 | 文件 | 职责 |
|------|------|------|
| `Constitution` | constitution.py | FSM 规则拦截器 |
| `Gateway` | gateway.py | 输出过滤网关 |
| `PTCEnforcer` | ptc_enforcer.py | **PTC 脚本强制** |

### 5. facilitator/ - 共识机制

| 类名 | 文件 | 职责 |
|------|------|------|
| `WaldConsensus` | wald_consensus.py | SPRT 共识算法 |
| `ShadowFacilitator` | shadow_facilitator.py | Flash→Pro 投机共识 |
| `Facilitator` | facilitator.py | 辩论管理 |

### 6. mcp/ - MCP 服务器

| 类名 | 文件 | 职责 |
|------|------|------|
| `ToolSearchTool` | tool_search.py | **动态工具发现** |
| `AICouncilServer` | ai_council_server.py | MCP 服务实现 |

## Token 效率实现

| Pattern | 实现位置 | Token 节省 |
|---------|----------|:----------:|
| Rolling Context | `context/rolling_context.py` | O(N)→O(1) |
| Gemini Cache | `context/gemini_cache.py` | ~90% |
| Auto-Compact | `context/auto_compact.py` | 阈值触发 |
| Tool Search | `mcp/tool_search.py` | 动态加载 |
| Protocol Buffers | `protocol/schema.py` | ~70% |
| Shadow Cabinet | `facilitator/shadow_facilitator.py` | ~90% |

## 2025年12月 模型分工

| 任务类型 | 推荐模型 | SWE-bench |
|---------|---------|:---------:|
| 规划/架构 | GPT 5.2 Codex | 78% |
| 日常编码 | Claude 4.5 Sonnet | 77.2% |
| 复杂重构 | Claude 4.5 Opus | **80.9%** |
| 全库审计 | Gemini 3 Pro | 1M ctx |
| 快速任务 | Gemini 3 Flash | 3x 速度 |

## 常用命令

```bash
# 测试
just test                         # 运行所有测试
just verify                       # compile + lint + test

# 开发
just dev "任务描述"               # 6步自愈工作流
just tdd                          # TDD 模式
just impl                         # 实现模式
```
