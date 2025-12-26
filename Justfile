set shell := ["bash", "-lc"]

# === 上下文治理 ===

codemap:
  @bash scripts/codemap.sh

# === 理事会命令 ===

plan TASK:
  @bash scripts/plan_codex.sh "{{TASK}}"

audit:
  @bash scripts/audit_gemini.sh

# === TDD/Impl (Gemini Flash 高频) ===

tdd-gemini:
  @bash scripts/tdd_gemini.sh

impl-gemini:
  @bash scripts/impl_gemini.sh

# === TDD/Impl (Claude 备用) ===

tdd:
  @echo "运行 /tdd <scope> 在 Claude Code 中"

impl:
  @echo "运行 /impl <scope> 在 Claude Code 中"

# === 测试与验证 ===

test:
  @source .venv/bin/activate && \
    if python -c 'import importlib.util,sys; sys.exit(0 if importlib.util.find_spec("pytest_cov") else 1)'; then \
      pytest -q --cov=src --cov-report=xml tests/; \
    else \
      pytest tests/ -q; \
    fi

compile:
  @python3 -m py_compile src/*.py

lint:
  @if [[ -x .venv/bin/ruff ]]; then .venv/bin/ruff check src tests tools; \
    elif command -v ruff >/dev/null 2>&1; then ruff check src tests tools; \
    else echo "skip: ruff not installed"; fi

# === 门禁 ===

verify: compile lint test
  @echo "✅ VERIFY PASS"

# === 交付 ===

ship: verify
  @echo "=== Codex Review ==="
  @codex review --diff HEAD~1 2>/dev/null || echo "Review: run 'codex' manually"
  @echo ""
  @echo "=== Git Status ==="
  @git status --short
  @echo ""
  @git log --oneline -3

# === 一键开发 ===

dev TASK:
  @just codemap
  @just plan "{{TASK}}"
  @echo ""
  @echo "📋 下一步:"
  @echo "  1. just audit (如需审计)"
  @echo "  2. just tdd-gemini 或 /tdd"
  @echo "  3. just impl-gemini 或 /impl"
  @echo "  4. just verify"
  @echo "  5. just ship"
