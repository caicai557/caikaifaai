---
description: 生成可测规格（验收/边界/风险/拆解）
argument-hint: [功能/节点/问题]
---
为“$ARGUMENTS”输出 SPEC（不写代码）：
- 目标与非目标
- 输入/输出（accountId/instanceId/chatId/messageId/ts）
- 状态机节点影响范围
- 验收标准（Given/When/Then ≥ 8 条，含失败兜底）
- 风险：乱序/重入/重连/去重/翻译失败/隔离串线
- 最小实现拆解（≤ 8 步，每步 1~2 小时）
