---
description: 生成 PR 描述并给出 gh 命令（先让我确认再执行）
allowed-tools: Bash(git status:*), Bash(git diff:*), Bash(git branch:*), Bash(git log:*), Bash(gh repo view:*), Bash(gh pr create:*), Bash(gh pr view:*)
argument-hint: [PR标题可选]
---
基于当前变更生成 PR（不要直接创建，先输出命令让我确认）：
- 标题：优先 $ARGUMENTS
- 描述必须含：动机/改动/验证/风险/监控点/回滚方案
- 输出一条可执行的 `gh pr create ...` 命令
