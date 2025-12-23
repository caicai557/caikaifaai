set shell := ["bash", "-lc"]

doctor:
  @command -v git >/dev/null || (echo "git missing" && exit 1)
  @command -v python3 >/dev/null || (echo "python3 missing" && exit 1)
  @command -v rg >/dev/null || echo "ripgrep (rg) missing: sudo apt-get install -y ripgrep"
  @command -v fd >/dev/null || echo "fd missing: sudo apt-get install -y fd-find (or fd)"
  @echo "OK: basic tooling present"
  @echo "Tip: ensure codex/gemini/claude are callable in this WSL shell."

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

verify:
  @echo "Run your project's test/build commands here (edit Justfile to wire real commands)."

ship:
  @echo "Checklist: .council/CHECKLIST.md"
