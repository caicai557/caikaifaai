---
description: 线性流程拆解为状态机 JSON（含翻译/去重/重连）
argument-hint: [流程名]
---
只输出 JSON（不要解释）：

{
  "flowName": "",
  "version": "0.2",
  "global": {
    "translation": {"enabled": true, "provider": "google", "source": "auto", "target": "zh", "timeoutMs": 3000, "retryMax": 2, "cacheTtlSec": 86400},
    "dedupe": {"key": "accountId+chatId+messageId", "fallbackKey": "hash(text+senderId+ts)", "ttlSec": 86400},
    "reconnect": {"strategy": "exp+jitter", "maxRetries": 8, "cooldownSec": 300},
    "chatConcurrency": "serial"
  },
  "nodes": [
    {"id":"N0","name":"","entry":{"when":""},"matchOn":"translatedText","replyKey":"SCRIPT_KEY","transitions":[{"when":"any","to":"N1"},{"when":"fallback","to":"NF"}],"telemetry":{"log":["event","nodeId","reason","dedupeKey"]}}
  ]
}

约束：
- 默认线性；分支深度 ≤ 3
- 每节点必须 fallback
- replyKey 必须来自话术库（不写长文）
- 翻译失败必须走 fallback 或人工接管（不能猜）
