#!/bin/bash
# codemap.sh - 生成代码地图

set -e

echo "# CODEMAP (Auto-generated)" > CODEMAP.md
echo "" >> CODEMAP.md
echo "## 目录结构" >> CODEMAP.md
echo '```' >> CODEMAP.md
find src tests -type f -name "*.py" 2>/dev/null | head -50 >> CODEMAP.md
echo '```' >> CODEMAP.md

echo "" >> CODEMAP.md
echo "## 模块签名" >> CODEMAP.md

for f in src/*.py; do
  if [ -f "$f" ]; then
    echo "" >> CODEMAP.md
    echo "### $f" >> CODEMAP.md
    echo '```python' >> CODEMAP.md
    grep -E "^(def |class |from |import )" "$f" 2>/dev/null | head -20 >> CODEMAP.md
    echo '```' >> CODEMAP.md
  fi
done

echo "Generated CODEMAP.md"
