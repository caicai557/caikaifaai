---
description: Council verify — run project verification and auto-fix failures.
argument-hint: [scope]
---

请执行项目验收命令，并把失败项按"根因→修复→回归验证"输出：

1) 运行：`just verify` 或 `bash scripts/verify.sh`
2) 若失败：只改最小必要文件修复
3) 复跑 verify 直到 PASS
4) 输出变更摘要 + 风险点 + 后续建议

Task / scope: $ARGUMENTS

Rules:

- 自愈循环：失败 → 读日志 → 修复 → 重试
- 最小改动原则
- 更新 .council/NOTES.md 记录验证结果
