#!/bin/bash
# plan_codex.sh - 调用 Codex 生成 SPEC.md

set -e

TASK="$1"

if [ -z "$TASK" ]; then
  echo "Usage: just plan \"<task description>\""
  exit 1
fi

echo "=== Codex Orchestrator ==="
echo "Task: $TASK"
echo ""
echo "请将以下 prompt 粘贴到 Codex CLI:"
echo ""
cat <<EOF
You are the Orchestrator.
Read: .council/BRIEF.md and CODEMAP.md (SSOT).
Task: $TASK

Output a SPEC.md with:
1) Problem statement + non-goals
2) Task tree (small steps; identify files to touch)
3) Acceptance criteria (testable)
4) Verify command(s): must end with \`just verify\`
5) Risks (top 5) + mitigations

Keep it short and executable.
EOF
