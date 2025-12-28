# Token 节省最佳实践 (2025)

> **核心原则**: 批量优于逐个，自动化优于手动。

## 黄金法则

```text
┌─────────────────────────────────────────┐
│  Token 节省检查清单                      │
├─────────────────────────────────────────┤
│ 在执行任何 Edit 操作前，问自己:          │
│                                         │
│ □ 这是 lint 错误吗？                    │
│   → YES: 用 ruff/black，不要 Edit      │
│                                         │
│ □ 需要修改 ≥3 处吗？                    │
│   → YES: 写批量脚本，不要逐个 Edit      │
│                                         │
│ □ 我确定这个方案能工作吗？              │
│   → NO: 先写 repro.py 本地验证          │
│                                         │
│ □ 这个操作我会重复吗？                  │
│   → YES: 写脚本自动化                   │
│                                         │
│ 记住: 每次 Edit ≈ 3k tokens            │
│      批量脚本 ≈ 2k tokens (一次性)      │
└─────────────────────────────────────────┘
```

## 场景对照表

| 场景 | ❌ 错误做法 | Token | ✅ 正确做法 | Token | 节省 |
|------|------------|-------|------------|-------|------|
| Lint E501 错误 | 逐个 Edit (6次) | 18k | `ruff check --fix` | 0.5k | 97% |
| Mock 试错 | 反复 Edit 尝试 | 21k | 本地验证 + 批量脚本 | 2.5k | 88% |
| 格式化 | 逐个修复 | 15k | `black .` | 0.3k | 98% |
| Import 排序 | 逐个调整 | 10k | `isort .` | 0.2k | 98% |

## 自动修复工具

```bash
# Lint 自动修复
ruff check --fix .                    # 修复所有可自动修复的问题
ruff check --select E501 --fix .      # 仅修复 line-too-long
ruff check --select F401 --fix .      # 仅修复 unused-import

# 格式化
black .                               # 格式化所有 Python 文件
isort .                               # 排序 import 语句

# 组合命令
ruff check --fix . && black . && isort .
```

## 批量替换模板

当需要修改 ≥3 处相同代码时：

```python
# scripts/batch_replace.py
import glob
import re

def batch_replace(pattern, replacement, file_glob="**/*.py"):
    files_changed = 0
    for filepath in glob.glob(file_glob, recursive=True):
        with open(filepath, 'r') as f:
            original = f.read()
        modified = re.sub(pattern, replacement, original, flags=re.MULTILINE)
        if modified != original:
            with open(filepath, 'w') as f:
                f.write(modified)
            print(f"✅ {filepath}")
            files_changed += 1
    print(f"\n总计修改: {files_changed} 个文件")
    return files_changed

if __name__ == "__main__":
    batch_replace(
        pattern=r'old_pattern',
        replacement='new_pattern',
        file_glob="src/**/*.py"
    )
```

## 预检查脚本

```python
# scripts/precheck_before_edit.py
def should_use_batch_tool(task):
    task = task.lower()
    checks = [
        ("lint", "ruff check --fix"),
        ("e501", "ruff check --select E501 --fix"),
        ("格式", "black ."),
        ("import", "isort ."),
        ("≥3", "编写批量脚本"),
        ("多个", "编写批量脚本"),
    ]
    for keyword, tool in checks:
        if keyword in task:
            return True, tool
    return False, None
```

## 实战流程

### 场景 1: 发现 Lint 错误

```bash
# 步骤 1: 直接自动修复
ruff check --fix .

# 步骤 2: 验证
just verify

# 完成！< 500 tokens
```

### 场景 2: 需要修改 10+ 处相同代码

```bash
# 步骤 1: 创建批量脚本
cat > scripts/fix_issue.py << 'EOF'
import glob, re
for f in glob.glob("src/**/*.py", recursive=True):
    with open(f) as file:
        content = file.read()
    content = re.sub(r'old', 'new', content)
    with open(f, 'w') as file:
        file.write(content)
EOF

# 步骤 2: 运行
python scripts/fix_issue.py

# 步骤 3: 验证
just verify

# 完成！< 2k tokens
```

### 场景 3: 不确定方案是否可行

```bash
# 步骤 1: 本地创建验证脚本
cat > repro.py << 'EOF'
# 测试代码
from unittest.mock import patch
# ... 验证逻辑
EOF

# 步骤 2: 本地运行验证
python repro.py

# 步骤 3: 确认可行后再 Edit
# (只有一次 Edit，不是反复试错)
```
