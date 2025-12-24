#!/usr/bin/env bash
set -euo pipefail
TASK="${1:-}"

if ! command -v codex >/dev/null 2>&1; then
  echo "codex not found in PATH" >&2
  exit 1
fi

if [[ -z "${TASK}" ]]; then
  echo "Usage: bash scripts/plan_codex.sh \"<task>\"" >&2
  exit 1
fi

BRIEF="$(sed -n '1,200p' .council/BRIEF.md 2>/dev/null || true)"
CODEMAP="$(sed -n '1,200p' CODEMAP.md 2>/dev/null || true)"

PROMPT=$(cat <<PROMPT_EOF
You are the Orchestrator. Your only job is to output a SPEC.md in Markdown.

SSOT:
- .council/BRIEF.md (below)
- CODEMAP.md excerpt (below)

Task: ${TASK}

Rules:
- Do NOT edit files.
- Do NOT run shell commands.
- Output ONLY the content for SPEC.md (no fences).

SPEC.md must include:
1) Problem statement + non-goals
2) Task tree (small steps)
3) Files to touch (exact paths)
4) Acceptance criteria (copy BRIEF; tighten if needed)
5) Verify commands (must end with: just verify)
6) Risks (top 5) + mitigations

BRIEF:
${BRIEF}

CODEMAP excerpt:
${CODEMAP}
PROMPT_EOF
)

# Non-interactive run; write final message to SPEC.md
printf "%s" "$PROMPT" | codex exec - \
  --sandbox read-only \
  --ask-for-approval never \
  --output-last-message SPEC.md

echo "Wrote SPEC.md"
