# AGENTS.md (Codex)

## 规则
- Small Diffs：每次改动尽量小
- 防御性编程：空值/异常/竞态必须处理
- 必须给出：验证命令 + 预期结果
- 禁止：无依据的大重构、引入大量新依赖

## 交付格式（强制 YAML）
- plan（步骤、文件、风险）
- diff（优先 unified diff）
- verification（命令+预期）
- rollback（回滚步骤）

---

## 模型分工规则 (Model Division of Labor)

### Gemini 3 Flash（默认 / 快引擎）
- 脚手架、简单功能实现、快速 refactor
- 生成样板、写小工具函数
- 把想法变成可跑原型
- **命令**: `gpf "prompt"`

### Gemini 3 Pro（按需 / 稳引擎）
- 复杂前端交互 / 状态机设计
- 并发与一致性
- 架构评审、风险扫描
- 长上下文审阅
- **命令**: `gpp "prompt"`

### Codex Max（生产线 / 加固引擎）
- 补边界条件、加测试
- 修隐蔽 bug、做防御式编程
- 保证可维护与可回滚
- **命令**: `cm` 或 `/codex_review`、`/codex_patch_plan`

### Claude Code（总包 / 编排引擎）
- 拆任务、写 plan + 验收
- 组织小 diff (≤200行)
- 串联 MCP 工具
- 输出可执行验证命令
- **命令**: `cc` 或 `claude`
