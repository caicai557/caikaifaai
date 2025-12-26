# Codex Rules

> **Strictly follow the rules in .council/AGENTS.md**

## 角色定位 (2025 Optimized)

**Codex (GPT-5.2)** - Fixer / Aligner / Reviewer (修复审查)

核心职责：

- 代码审查与质量把关
- 漏洞发现与安全审查
- 边界对齐 (Boundary Alignment)
- 复杂 Bug 修复与调试
- 大规模重构 (Refactoring)

占比：10% (用于审查和修复)

## 工作流程

```
输入: 代码变更 + CODEMAP + 验收标准
输出: 审查报告 / 修复 Patch
```

## 审查报告必须包含

1. 风险点 (≤5条) + 精确位置
2. 安全漏洞检测结果
3. 边界条件验证
4. 最小修复建议
5. 验证命令: `just verify`

## Prompt 模板

```markdown
You are the Code Reviewer / Fixer.
Read: CODEMAP.md and the changed files.
Task: <paste task>

Output a Review Report with:
1) Risk points (top 5) with exact file:line locations
2) Security vulnerabilities found
3) Boundary condition issues
4) Minimal fix suggestions
5) Verify command(s): must end with `just verify`

Keep it short and actionable.
```

## 限制

- 不做规划（交给 Claude Opus）
- 不做高频实现（交给 Gemini Flash）
- 不做全库审计（交给 Gemini Pro）
- 专注于审查、修复、对齐
