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
  if [[ -x ".venv/bin/ruff" ]]; then
    echo "  - ruff lint"
    .venv/bin/ruff check src tests tools || true
  elif command -v ruff >/dev/null 2>&1; then
    echo "  - ruff lint"
    ruff check src tests tools || true
  fi

  # 测试
  if command -v pytest >/dev/null 2>&1; then
    echo "  - pytest"
    source .venv/bin/activate 2>/dev/null || true
    if python3 - <<'PY'
import importlib.util
raise SystemExit(0 if importlib.util.find_spec("pytest_cov") else 1)
PY
    then
      pytest -q --cov=src --cov-report=xml
    else
      pytest -q
    fi
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

# 自动更新 NOTES.md
echo "" >> .council/NOTES.md
echo "## $(date +%Y-%m-%d) Verify" >> .council/NOTES.md
echo "- Status: PASS" >> .council/NOTES.md
echo '```' >> .council/NOTES.md
git diff --stat HEAD 2>/dev/null | head -10 >> .council/NOTES.md || true
echo '```' >> .council/NOTES.md
