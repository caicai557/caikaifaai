---
description: 闸门式 Review（必审：隔离/去重/重连/乱序）
allowed-tools: Bash(git diff:*), Bash(git status:*), Bash(git log:*), Bash(find:*), Bash(cat:*)
argument-hint: [审查重点可选]
---
对当前变更做闸门审查（重点：$ARGUMENTS）：

1) 阻塞合并（必须修）
2) 建议修（不阻塞）
3) 风险提示（上线注意）
强制覆盖：多开隔离、幂等去重、异常重连、乱序与重入、翻译失败兜底、日志字段完整性
