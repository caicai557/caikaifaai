# 项目协作契约（Claude Code）

> [!IMPORTANT]
> **必须严格遵循**: 在执行任何任务前,请先阅读并遵守 [AGENTS.md](file:///home/dabah123/projects/caicai/AGENTS.md) 中的所有规则和模型分工。AGENTS.md 是智能体理事会的"单一事实来源"。

## 目标
- 小步交付（Small Diffs）
- 任何改动必须可验证、可回滚
- 默认不做大重构

## 工作流（强制）
1) 先输出 plan（≤30行）+ 验收命令
2) 再改代码（尽量 ≤200 行 diff）
3) 跑验收命令并贴结果
4) 输出交接（YAML/JSON）

## 何时调用谁
- 快速草稿/样板/简单实现：优先 Gemini Flash（gpf）
- 前端复杂交互/状态机/架构权衡：用 Gemini Pro（gpp）做评审
- 生产加固/边界条件/测试：交给 Codex（通过 MCP codex 工具或 cm）

## MCP 工具
- `/codex_review` - 风险扫描
- `/codex_patch_plan <目标>` - 最小补丁计划
- `council-memory` - 会话持久化和知识图谱

## 智能体理事会 (Agent Council)

> [!TIP]
> 使用 `council` 模块协调多智能体协作

```python
from council.agents import Architect, Coder, SecurityAuditor
from council.facilitator import Facilitator, ConsensusDecision
from council.governance import GovernanceGateway, ActionType
```

### 专家角色
| 角色 | 职责 | 立场 |
|------|------|------|
| Architect | 顶层设计、架构评审 | 长期可维护性 |
| Coder | 代码实现、TDD | Small Diffs |
| SecurityAuditor | 漏洞扫描、攻击面分析 | 怀疑论者 |

### Wald 共识算法
- **π ≥ 0.95**: 自动提交 (AUTO_COMMIT)
- **π ≤ 0.30**: 拒绝 (REJECT)
- **其他**: 人工审核 (HOLD_FOR_HUMAN)

## HITL 治理流程

> [!CAUTION]
> 以下操作**必须经过人工审批**:

| 操作类型 | 风险级别 | 审批要求 |
|----------|----------|----------|
| DEPLOY | Critical | 强制 |
| DATABASE | Critical | 强制 |
| SECURITY | Critical | 强制 |
| FILE_DELETE | High | 强制 |
| CONFIG_CHANGE | Medium | 推荐 |

### 审批流程
```
1. 检查是否需要审批
   → GovernanceGateway.requires_approval(action_type, paths)

2. 创建审批请求
   → gateway.create_approval_request(...)

3. 等待董事长签字
   → gateway.approve(request_id) 或 gateway.reject(request_id)
```

### 受保护路径 (自动触发审批)
- `deploy/**`, `config/production/**`
- `.env*`, `secrets/**`
- `*.key`, `*.pem`

## 硬性约束
1. 所有交接 → 一律 YAML/JSON
2. 所有改动 → 一律 Small diffs（≤200行）
3. 所有任务 → 一律带 verification
4. **高风险操作 → 一律经 HITL 网关审批**

