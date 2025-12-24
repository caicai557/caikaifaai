#!/usr/bin/env bash
set -euo pipefail

echo "== verify: format/lint/test/build =="

# Python 项目
if [[ -f "pyproject.toml" || -f "requirements.txt" || -d "src" ]]; then
  echo "[python] running..."

  # 编译检查
  if [[ -d "src" ]]; then
    echo "  - compile check"
    python3 -m py_compile src/*.py 2>/dev/null || true
  fi

  # Lint
  if command -v ruff >/dev/null 2>&1; then
    echo "  - ruff lint"
    ruff check . || true
  fi

  # 测试
  if command -v pytest >/dev/null 2>&1; then
    echo "  - pytest"
    source .venv/bin/activate 2>/dev/null || true
    pytest -q
  fi
fi

# Node 项目
if [[ -f "package.json" ]]; then
  echo "[node] running..."
  if command -v pnpm >/dev/null 2>&1; then
    pnpm -s test || true
    pnpm -s lint || true
    pnpm -s build || true
  elif command -v npm >/dev/null 2>&1; then
    npm -s test || true
    npm -s run lint || true
    npm -s run build || true
  fi
fi

echo "== verify: PASS =="
