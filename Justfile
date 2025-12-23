set shell := ["bash", "-lc"]

# === Environment ===

doctor:
  @command -v python3 >/dev/null || (echo "python3 missing" && exit 1)
  @command -v git >/dev/null || (echo "git missing" && exit 1)
  @echo "OK: base tools"

# === Code Quality ===

# Format code (requires ruff)
fmt:
  @if command -v ruff >/dev/null 2>&1; then ruff format .; else echo "skip: ruff not installed"; fi

# Lint code (requires ruff)
lint:
  @if command -v ruff >/dev/null 2>&1; then ruff check .; else echo "skip: ruff not installed"; fi

# Type check (requires mypy)
type:
  @if command -v mypy >/dev/null 2>&1; then mypy src --ignore-missing-imports; else echo "skip: mypy not installed"; fi

# Compile check (cheap sanity)
compile:
  @python3 -m py_compile src/*.py

# === Testing ===

# Run all tests
test:
  @source .venv/bin/activate && pytest tests/ -q

# Run contract tests only
test-contracts:
  @source .venv/bin/activate && pytest tests/test_contracts.py -v

# === Gates ===

# Single source of truth gate (before commit)
verify: compile lint test
  @echo "✅ VERIFY PASS"

# === Workflow ===

codemap:
  @python3 scripts/codemap.py > CODEMAP.md
  @echo "Generated CODEMAP.md"

plan:
  @echo "Open Codex CLI and paste: .council/prompts/plan_codex.md (fill <PASTE_TASK_HERE>)"

audit:
  @echo "Open Gemini CLI and paste: .council/prompts/audit_gemini.md"

tdd:
  @echo "Open Claude Code and paste: .council/prompts/tdd_claude.md"

impl:
  @echo "Open Claude Code and paste: .council/prompts/implement_claude.md"

ship:
  @echo "=== Shipping Checklist ==="
  @cat .council/CHECKLIST.md
  @echo ""
  @echo "=== Git Status ==="
  @git status --short
  @echo ""
  @echo "=== Recent Commits ==="
  @git log --oneline -3
