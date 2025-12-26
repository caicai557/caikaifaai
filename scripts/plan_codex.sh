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

CODEX_HOME_CANDIDATE="${CODEX_HOME:-$HOME/.codex}"
mkdir -p "${CODEX_HOME_CANDIDATE}" 2>/dev/null || true
if ! touch "${CODEX_HOME_CANDIDATE}/.codex_write_test" 2>/dev/null; then
  CODEX_HOME_CANDIDATE="$(pwd)/.codex"
  mkdir -p "${CODEX_HOME_CANDIDATE}"
else
  rm -f "${CODEX_HOME_CANDIDATE}/.codex_write_test"
fi
CODEX_HOME_PARENT="$(dirname "${CODEX_HOME_CANDIDATE}")"
mkdir -p "${CODEX_HOME_PARENT}" 2>/dev/null || true
export CODEX_HOME="${CODEX_HOME_CANDIDATE}"

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

OUTPUT_FLAG=""
if command -v rg >/dev/null 2>&1; then
  if codex exec --help 2>/dev/null | rg -q -- "--output-last-message"; then
    OUTPUT_FLAG="--output-last-message"
  elif codex exec --help 2>/dev/null | rg -q -- "-o, --output-last-message"; then
    OUTPUT_FLAG="-o"
  fi
else
  if codex exec --help 2>/dev/null | grep -q -- "--output-last-message"; then
    OUTPUT_FLAG="--output-last-message"
  elif codex exec --help 2>/dev/null | grep -q -- "-o, --output-last-message"; then
    OUTPUT_FLAG="-o"
  fi
fi

# Non-interactive run; write final message to SPEC.md
if [[ -n "${OUTPUT_FLAG}" ]]; then
  printf "%s" "$PROMPT" | env HOME="${CODEX_HOME_PARENT}" CODEX_HOME="${CODEX_HOME}" \
    codex exec - \
    --sandbox read-only \
    "${OUTPUT_FLAG}" SPEC.md
else
  printf "%s" "$PROMPT" | env HOME="${CODEX_HOME_PARENT}" CODEX_HOME="${CODEX_HOME}" \
    codex exec - \
    --sandbox read-only > SPEC.md
fi

echo "Wrote SPEC.md"
