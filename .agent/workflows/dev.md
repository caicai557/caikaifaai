---
description: 运行开发任务 - 自动加载2025最佳实践
---

# /dev 工作流

## 步骤

1. 初始化 DevOrchestrator
2. 加载 ProjectMemory (CLAUDE.md 配置)
3. 启用 SemanticCache
4. 执行任务

## 命令

```bash
# 启动开发流程
python -c "
from council.dev_orchestrator import DevOrchestrator
import asyncio

orch = DevOrchestrator(working_dir='.')
result = asyncio.run(orch.dev('你的任务描述'))
print(result)
"
```
