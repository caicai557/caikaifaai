---
description: 日志与观测性方案（事件/字段/采样/隐私）
argument-hint: [模块/链路名]
---
为“$ARGUMENTS”设计日志与观测：

1) 事件列表（进入节点、发送、收到、判定、超时、重连、限流）
2) 必备字段（accountId, sessionId, nodeId, messageId, reason, ts）
3) 采样策略（避免日志爆炸）
4) 隐私/合规：不要记录敏感内容（token/验证码/隐私文本）
5) 3 个常见故障如何靠日志定位（示例）
