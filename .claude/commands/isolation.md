---
description: 多开隔离落地（partition/目录/验收）
argument-hint: [账号策略说明可选]
---
输出 Electron 多开隔离方案：
1) partition 命名（强制 persist:acc_<accountId>）
2) 每账号隔离资源清单（session/cookies/cache/log/tmp/download）
3) IPC 路由规范（必须携带 accountId/instanceId）
4) 隔离验收 ≥ 10 条（含重启后会话保持/不串线）
5) 典型串线根因与防线
