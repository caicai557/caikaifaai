---
description: 最小验证闭环（自动测试优先，否则手动回归脚本）
allowed-tools: Bash(npm test:*), Bash(npm run:*), Bash(git diff:*), Bash(git status:*), Bash(cat:*), Bash(find:*), Bash(ls:*)
argument-hint: [验证目标/场景]
---
围绕“$ARGUMENTS”输出并执行最小验证：
1) 识别可用测试入口（无则明确“缺失”）
2) 若无测试：输出手动回归脚本（步骤+预期）
3) 运行必要命令（只跑安全且必要的）
4) 输出证据（命令+结果摘要），失败给定位建议
