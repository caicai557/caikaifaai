#!/usr/bin/env bash
set -euo pipefail

if ! command -v gemini >/dev/null 2>&1; then
  echo "gemini not found in PATH" >&2
  exit 1
fi

if [[ ! -f SPEC.md ]]; then
  echo "SPEC.md missing. Run: just plan \"<task>\" first." >&2
  exit 1
fi

INPUT="$(mktemp)"
{
  echo "=== BRIEF ==="
  sed -n '1,200p' .council/BRIEF.md 2>/dev/null || true
  echo
  echo "=== CODEMAP ==="
  sed -n '1,200p' CODEMAP.md 2>/dev/null || true
  echo
  echo "=== SPEC ==="
  sed -n '1,240p' SPEC.md
} > "$INPUT"

cat "$INPUT" | gemini '
You are the Auditor.
Goal: find cross-file conflicts, missing edge cases, and API/exception contract issues.

Output ONLY AUDIT.md content (Markdown), including:
- Conflicts / integration risks
- Contract clarifications (errors, types)
- Minimum test set
- Minimal revisions to SPEC (if needed)
Keep it short and actionable.
' > AUDIT.md

rm -f "$INPUT"
echo "Wrote AUDIT.md"

PYTHON_BIN="python3"
if [[ -x ".venv/bin/python" ]]; then
  PYTHON_BIN=".venv/bin/python"
fi
"${PYTHON_BIN}" scripts/graph_builder.py build
