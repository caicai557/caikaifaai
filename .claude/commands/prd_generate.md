---
description: "PRD 生成: 将模糊需求转化为结构化产品需求文档和任务树"
---

# PRD 生成命令

## 用途
将用户的模糊指令转化为结构化的 PRD（产品需求文档）和任务树。

## 主控者
**Codex (GPT-5.1/5.2)** - 担任 Orchestrator 角色

## 执行方式
```bash
# 通过 MCP 调用 codex 工具
codex "Generate PRD: $ARGUMENTS"
```

## 输出格式 (YAML)

```yaml
prd:
  title: "功能名称"
  background: |
    为什么需要这个功能？当前痛点是什么?
  
  objectives:
    - 目标1: 可衡量的成功指标
    - 目标2: 用户价值
  
  scope:
    in_scope:
      - 包含的功能点1
      - 包含的功能点2
    out_of_scope:
      - 明确不包含的内容
  
  user_stories:
    - as: "角色"
      i_want: "需求"
      so_that: "价值"
      acceptance_criteria:
        - 验收条件1
        - 验收条件2
  
  technical_considerations:
    - 技术约束1
    - 技术约束2
  
  risks:
    - risk: "潜在风险"
      mitigation: "缓解措施"

task_tree:
  - id: "T1"
    name: "主任务1"
    owner: "Gemini Flash | Gemini Pro | Codex | Claude"
    priority: "P0 | P1 | P2"
    estimated_effort: "S | M | L | XL"
    dependencies: []
    subtasks:
      - id: "T1.1"
        name: "子任务1"
        files_affected:
          - path/to/file1.ts
        verification:
          cmd: "npm test -- path/to/test"
          expected: "所有测试通过"

verification:
  - cmd: "cat prd_output.yaml | yq '.prd.title'"
    expected: "显示 PRD 标题"
```

## 使用示例

```bash
# 在 Claude Code 中调用
/prd_generate "添加用户登录功能,支持邮箱+密码登录"
```

## 验证步骤
1. 检查输出是否符合 YAML 格式
2. 验证任务树是否覆盖所有 user stories
3. 确认每个任务分配了正确的 owner (依据 AGENTS.md)
4. 检查是否包含验收标准

## 下游命令
- PRD 批准后 → `/audit_design` (架构审计)
- 任务树确认后 → `/tdd_tests` (生成测试)
