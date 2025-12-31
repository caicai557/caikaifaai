# Council - Multi-Model Agent Framework (v1.0.0)

Council 是一个符合 2025 年 12 月最佳实践的生产级多模型智能体框架。它集成了 Claude 4.5、Gemini 3 和 GPT-5.2 (模拟) 的能力，提供智能的开发编排。

## 🚀 快速开始 (Quick Start)

### 1. 安装 (Installation)

推荐采用 **In-Repo Agent** 模式（最佳实践），将 Council 直接集成到你的项目中：

1. 将 `council` 文件夹复制到你的项目根目录。
2. 安装依赖：

    ```bash
    pip install -r council/requirements.txt
    # (如果没有 requirements.txt，主要依赖是: google-generativeai, openai, pydantic, pytest)
    ```

### 2. 配置 (Configuration)

设置环境变量：

```bash
export GEMINI_API_KEY="your-gemini-key"
export OPENAI_API_KEY="your-openai-key"  # 可选
export PYTHONPATH=$PYTHONPATH:.          # 确保能导入 council
```

### 3. 使用 (Usage)

#### 命令行模式 (CLI)

```bash
# 开发任务 (自动编排 EPCC 流程)
python -m council.cli dev "实现用户登录功能，包含 JWT 验证"

# 任务分类与模型推荐
python -m council.cli classify "重构数据库连接池"

# 路由决策
python -m council.cli route "修复内存泄漏 bug"
```

#### Claude Code 集成 (最佳体验)

将 `council/CLAUDE.md` 的内容复制到你项目的 `CLAUDE.md` 中。然后直接使用 Slash Commands：

- `/council-dev "任务描述"` - 全自动开发
- `/council-classify "任务描述"` - 查看 AI 建议的模型
- `/council-test` - 运行自愈测试循环

## 🏆 2025 最佳实践 (Best Practices)

Council 的设计遵循以下核心原则，建议在使用时也予以采纳：

1. **In-Repo Agent (代码即智能体)**
    - **做法**: 不要把 Agent 当作黑盒外部工具，而是将其代码放在项目仓库中 (`/council`)。
    - **好处**: Agent 的行为可以像业务代码一样被版本控制、审查和定制。

2. **Context-Aware (上下文感知)**
    - **做法**: 维护 `CLAUDE.md` 和 `.editorconfig`。
    - **好处**: Agent 自动读取这些文件，理解项目规范、架构决策和代码风格，无需每次重复提示。

3. **Protocol-First Communication (协议优先)**
    - **做法**: Agent 之间使用结构化数据 (JSON/Pydantic) 而非自然语言对话。
    - **好处**: 节省 70% Token，消除歧义，便于程序化处理。

4. **Security by Default (默认安全)**
    - **做法**: 启用工具白名单 (`ToolAllowlist`)。
    - **好处**: 防止 Agent 误删文件或执行危险命令。所有敏感操作需显式授权。

5. **Observability (可观测性)**
    - **做法**: 关注 Token 使用量和成本 (`TokenTracker`)。
    - **好处**: 实时掌握 AI 算力成本，避免预算失控。

## 🎯 场景化使用指南 (Scenarios)

### 场景 A: 从零开发新模块

**推荐流程**:

1. **分类**: `python -m council.cli classify "设计并实现一个新的支付网关模块"`
    - *预期结果*: 推荐 `PLANNING` 任务类型，使用 `GPT-5.2 Codex` 或 `Claude Opus`。
2. **执行**: `python -m council.cli dev "设计并实现一个新的支付网关模块"`
    - *Council 行为*: Architect 先输出设计文档 -> 用户确认 -> Coder 生成代码 -> Coder 生成测试 -> 循环修复。

### 场景 B: 修复遗留 Bug

**推荐流程**:

1. **路由**: `python -m council.cli route "修复 user_service.py 中的空指针异常"`
    - *预期结果*: 路由到 `DEBUGGING` 专家 (Claude Sonnet)。
2. **执行**: `python -m council.cli dev "修复 user_service.py 中的空指针异常"`
    - *Council 行为*: 直接定位文件 -> 复现测试失败 -> 生成修复补丁 -> 验证通过。

### 场景 C: 全库代码审计/重构

**推荐流程**:

1. **配置**: 确保 `ToolAllowlist` 允许遍历整个 `src/` 目录。
2. **执行**: `python -m council.cli dev "审计 src/ 下所有 Python 文件的类型注解，确保符合 MyPy 标准"`
    - *Council 行为*: 可能会触发 `GEMINI_PRO` (1M Context) 进行全量分析，然后分批次进行修改。

## 📂 目录结构

- `agents/`: 专家智能体 (Architect, Coder, Reviewer)
- `dev_orchestrator.py`: 核心状态机编排器
- `persistence/`: 状态持久化 (SQLite)
- `observability/`: Token 追踪
- `mcp/`: 工具执行与安全沙箱
- `self_healing/`: 自动测试与修复循环
