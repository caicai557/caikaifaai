---
description: 检查点记录 — 完成任务、提交代码、更新笔记
argument-hint: [任务标签]
---

Follow the project rules and governance:

- Read and follow: .council/AGENTS.md and .council/CLAUDE.md
- Primary outputs: Git commit, .council/NOTES.md update

Task / label: $ARGUMENTS

Execution sequence:

1) Run `just verify` one last time to ensure green state.
2) If verify passes:
   - Git add all relevant changes
   - Git commit with message: "feat: $ARGUMENTS" (or suitable type)
3) Update `.council/NOTES.md` with a summary of the completed task.
4) (Optional) Update `.last_checkpoint` with current commit hash.

Output requirements:

- Commit hash
- Summary of changes
- Verification status (PASS)
