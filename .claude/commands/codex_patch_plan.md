---
description: "Codex 最小补丁计划：小步改动、可回滚、可验证"
---

请调用 codex MCP 工具，目标：$ARGUMENTS
输出（不超过 200 行）：

plan:
  - step:
    files:
    change:
diff: |
  (尽量给 unified diff；给不了就给精确替换片段)
verification:
  - cmd:
    expected:
rollback:
  - step:
