set shell := ["bash", "-lc"]

# === 上下文治理 ===

codemap:
  @bash scripts/codemap.sh

# === 理事会命令 ===

plan TASK:
  @bash scripts/plan_codex.sh "{{TASK}}"

audit:
  @bash scripts/audit_gemini.sh

# === 测试与验证 ===

test:
  @source .venv/bin/activate && pytest tests/ -q

compile:
  @python3 -m py_compile src/*.py

lint:
  @if command -v ruff >/dev/null 2>&1; then ruff check .; else echo "skip: ruff not installed"; fi

# === 门禁 ===

verify: compile lint test
  @echo "✅ VERIFY PASS"

# === 工作流 ===

tdd:
  @echo "运行 /tdd <scope> 在 Claude Code 中"

impl:
  @echo "运行 /impl <scope> 在 Claude Code 中"

ship:
  @echo "=== Ship Checklist ==="
  @git status --short
  @echo ""
  @git log --oneline -3
