#!/usr/bin/env bash
set -euo pipefail

mkdir -p .council/prompts scripts

# ---- Governance: AGENTS.md ----
cat > .council/AGENTS.md <<'EOF'
# Agent Council Governance (SSOT)

## Hard Safety Boundaries (Non-negotiable)
- DO NOT read, print, or exfiltrate secrets: .env, *.pem, *key*, credentials files.
- DO NOT run destructive commands (rm -rf, format disk, chmod -R on system paths).
- Any dependency installation must be explicit and minimal.
- All changes must be reviewable (diff-first), reversible (git), and test-verified.

## Definition of Done (DoD)
- Tests added/updated.
- Lint/typecheck pass (if applicable).
- Clear rollback plan (git commit history is clean).
- Updates documented in .council/NOTES.md and .council/DECISIONS.md (when architectural).

## Roles (Default)
- Codex: Orchestrator (PRD → task tree → acceptance criteria).
- Gemini: Auditor (cross-file conflicts, edge cases, design review).
- Claude Code: Executor (apply patches, write tests, run commands, iterate).
EOF

# ---- Project Rules: CLAUDE.md ----
cat > .council/CLAUDE.md <<'EOF'
# Project Engineering Rules (Enforced)

Strictly follow the rules in: ./.council/AGENTS.md

## Engineering Standards
- Prefer small PRs (<= 400 LOC net change) unless approved by a written decision.
- "Diff-first": propose plan, then patch, then verify.
- TDD preference: tests before logic for non-trivial changes.
- Deterministic commands: every workflow must be runnable from Justfile.

## Output Contracts
- Every task produces:
  1) Spec/Plan (what & why)
  2) Patch (code)
  3) Verification (tests/logs)
  4) Notes update (what changed)
EOF

# ---- SSOT Brief ----
cat > .council/BRIEF.md <<'EOF'
# BRIEF (Single Source of Truth)

## Goal
- (Fill) What are we building / changing?

## Constraints
- (Fill) Safety, platform, performance, non-goals.

## Current Architecture
- (Fill) Key modules, entrypoints, data flow.

## Acceptance Criteria
- (Fill) Observable pass conditions (tests, UI behavior, metrics).

## Commands
- (Fill) How to run, test, build, lint.
EOF

# ---- Decisions & Notes ----
cat > .council/DECISIONS.md <<'EOF'
# Architectural Decisions Log (ADL)

Use this format:
- Date:
- Decision:
- Context:
- Alternatives:
- Consequences:
EOF

cat > .council/NOTES.md <<'EOF'
# Iteration Notes (Session Summary)

After each task:
- What was attempted?
- What changed?
- What remains?
- Risks / follow-ups
EOF

cat > .council/CHECKLIST.md <<'EOF'
# Shipping Checklist

## Before coding
- [ ] BRIEF updated
- [ ] Code Map generated (CODEMAP.md)
- [ ] Task has acceptance criteria

## Before commit
- [ ] Tests added/updated
- [ ] All checks pass locally
- [ ] NOTES updated
- [ ] If architecture changed: DECISIONS entry added

## Before merge
- [ ] PR description includes plan + verification evidence
- [ ] Rollback plan clear
EOF

# ---- Prompts (you will paste into each CLI) ----
cat > .council/prompts/plan_codex.md <<'EOF'
You are the Orchestrator. Use .council/AGENTS.md and .council/BRIEF.md as SSOT.
Task: <PASTE_TASK_HERE>

Output:
1) PRD (problem, users, non-goals)
2) Task tree (phases, files likely touched)
3) Acceptance criteria (testable)
4) Risk register (top 5)
5) Minimal patch strategy (small PR first)
EOF

cat > .council/prompts/audit_gemini.md <<'EOF'
You are the Auditor. Read CODEMAP.md + existing code constraints in .council/BRIEF.md.
Goal: detect cross-file conflicts, missing edge cases, and better design alternatives.

Output:
- Conflicts & integration risks
- Required interface contracts
- Test strategy (what must be covered)
- Performance/security concerns
- A revised plan (if needed)
EOF

cat > .council/prompts/tdd_claude.md <<'EOF'
You are the QA engineer and Executor. Follow .council/AGENTS.md and .council/CLAUDE.md.
Write tests FIRST for the acceptance criteria. If unclear, propose assumptions explicitly.

Output:
- Test plan (list)
- Concrete test files/edits
- Commands to run
EOF

cat > .council/prompts/implement_claude.md <<'EOF'
You are the Executor. Follow .council/AGENTS.md and .council/CLAUDE.md.
Implement minimal changes to satisfy tests and acceptance criteria.

Output:
- Patch plan (diff-first)
- Apply code changes
- Run verification commands
- Update .council/NOTES.md (+ DECISIONS if needed)
EOF

# ---- Justfile ----
cat > Justfile <<'EOF'
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
EOF

# ---- Code Map generator ----
cat > scripts/codemap.py <<'EOF'
#!/usr/bin/env python3
import os, subprocess, sys
from pathlib import Path

def sh(cmd):
    return subprocess.check_output(cmd, shell=True, text=True, errors="replace")

root = Path(".").resolve()

print("# CODEMAP\n")
print("## Repo Summary\n")
try:
    branch = sh("git rev-parse --abbrev-ref HEAD").strip()
    head = sh("git rev-parse --short HEAD").strip()
    print(f"- Branch: {branch}")
    print(f"- HEAD: {head}\n")
except Exception:
    print("- Not a git repo (or git not available)\n")

print("## Top-level Structure\n")
for p in sorted([x for x in root.iterdir() if x.name not in [".git"]], key=lambda x: x.name.lower()):
    if p.is_dir():
        print(f"- {p.name}/")
    else:
        print(f"- {p.name}")

print("\n## Largest Files (tracked)\n")
try:
    out = sh("git ls-files -z | xargs -0 -I{} bash -lc 'wc -c \"{}\"' | sort -nr | head -n 25")
    print("```")
    print(out.strip())
    print("```")
except Exception as e:
    print(f"(skip: {e})")

print("\n## Grep Hotspots (common entrypoints)\n")
patterns = [
    "main(", "createApp", "app.listen", "Router", "index.ts", "index.js",
    "Electron", "BrowserWindow", "BrowserView", "express(", "fastify"
]
print("```")
for pat in patterns:
    try:
        lines = sh(f"rg -n \"{pat}\" -S . | head -n 10")
        if lines.strip():
            print(f"\n# {pat}\n{lines.strip()}")
    except Exception:
        pass
print("```")

print("\n## Council Files\n")
print("- Governance: .council/AGENTS.md")
print("- Rules: .council/CLAUDE.md")
print("- Brief (SSOT): .council/BRIEF.md")
print("- Decisions: .council/DECISIONS.md")
print("- Notes: .council/NOTES.md")
EOF
chmod +x scripts/codemap.py

echo "Bootstrap complete."
echo "Next:"
echo "  1) Install just (recommended): sudo apt-get update && sudo apt-get install -y just"
echo "  2) Run: just doctor"
echo "  3) Run: just codemap"
