---
description: 运行测试套件
---

# /test 工作流

## 步骤

// turbo-all

1. 运行完整测试

```bash
pytest tests/ -v --tb=short
```

1. 运行快速测试 (跳过外部依赖)

```bash
pytest tests/ -v --ignore=tests/council --ignore=tests/e2e
```

1. 检查覆盖率

```bash
pytest tests/ --cov=council --cov-report=term-missing
```
