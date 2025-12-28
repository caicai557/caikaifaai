#!/usr/bin/env bash
set -euo pipefail

# Check for claude CLI
if ! command -v claude >/dev/null 2>&1; then
  echo "Error: 'claude' CLI not found in PATH." >&2
  exit 1
fi

TASK="${1:-}"
if [[ -z "$TASK" ]]; then
  echo "Usage: $0 \"<task description>\"" >&2
  exit 1
fi

# Ensure .council directory exists
mkdir -p .council

# Prepare input context
INPUT_CONTEXT="$(mktemp)"
{
  echo "=== CODEMAP ==="
  # Read first 500 lines of CODEMAP to give context without blowing tokens
  sed -n '1,500p' CODEMAP.md 2>/dev/null || echo "CODEMAP.md not found"
  echo
  echo "=== EXISTING BRIEF ==="
  cat .council/BRIEF.md 2>/dev/null || echo "No existing BRIEF."
} > "$INPUT_CONTEXT"

# Construct Prompt
PROMPT="
You are Claude Opus 4.5, the Planning Agent (PM).
Your goal is to analyze the user request and generate a formal Product Requirements Document (PRD).

User Request: \"$TASK\"

Context:
$(cat "$INPUT_CONTEXT")

Output Requirements:
1.  **Problem Statement**: Current state, Target state, Non-goals.
2.  **User Stories**: As a [role], I want [feature], so that [benefit].
3.  **Acceptance Criteria (AC)**: List of verifiable conditions (checkboxes).
4.  **Task Tree**: Breakdown of subtasks (3-7 items) with file paths and complexity.
5.  **Model Distribution**: Suggest which model (Gemini Pro/Flash, Codex) to use for each phase.

Format: Markdown.
Output ONLY the content for .council/BRIEF.md. Do not include conversational filler.
"

echo "🤖 Planning Agent (Claude Opus) is thinking..."
echo "Task: $TASK"

# Execute Claude
# Using -p for non-interactive print mode
# Using --model opus as per 2025 standard
claude -p "$PROMPT" --model opus > .council/BRIEF.md

rm -f "$INPUT_CONTEXT"

echo "✅ Plan generated in .council/BRIEF.md"
echo "Next: Run 'just audit' to check for conflicts, or 'just tdd-gemini' to start coding."
