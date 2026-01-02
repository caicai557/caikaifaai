---
description: 代码质量检查和格式化
---

# /lint 工作流

## 步骤

// turbo-all

1. 运行 Ruff 检查

```bash
ruff check .
```

1. 自动修复可修复的问题

```bash
ruff check . --fix
```

1. 格式化代码

```bash
ruff format .
```
