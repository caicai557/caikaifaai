---
description: "Codex 快速审查：只给风险点+精确位置+最小修复建议"
---

请调用 codex MCP 工具，对当前仓库输出 YAML（必须结构化）：

risks:
  - severity: blocker|major|minor
    title:
    location: "path:line or symbol"
    why:
    minimal_fix:
verification:
  - cmd:
    expected:
