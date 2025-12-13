---
description: 上电自检（结构/脚本/入口/风险），补齐 TBD
allowed-tools: Bash(git status:*), Bash(git rev-parse:*), Bash(ls:*), Bash(find:*), Bash(node:*), Bash(npm:*), Bash(pnpm:*), Bash(yarn:*), Bash(gh:*), Bash(claude mcp list:*)
argument-hint: [今天要做的目标]
---
做一次“上电检查”，并输出最小可交付计划（最多 5 步）：

1) 环境：git / node / npm / gh（有哪个算哪个）+ `claude mcp list`
2) 项目结构：入口、主进程、渲染进程、BrowserView 管理位置
3) 运行方式：如何 dev 启动、如何构建、如何验证（缺失必须写“缺失”）
4) 风险：隔离/去重/重连/乱序四项最可能失败点
5) 今日最小计划：每步必须可验证、可回滚
